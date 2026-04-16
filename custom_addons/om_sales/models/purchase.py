from odoo import models, fields, api
from odoo.exceptions import UserError

123
class PurchaseOrder(models.Model):
  _name = 'sm.purchase.order'
  _description = 'Đơn Mua Hàng'
  _inherit = ['mail.thread', 'mail.activity.mixin']
  _order = 'id desc'

  name = fields.Char(string='Mã Đơn', required=True, copy=False, readonly=True, index=True, default='Mới')
  vendor_name = fields.Char(string='Nhà cung cấp', required=True, tracking=True)
  date_order = fields.Datetime(string='Ngày Đặt Hàng', default=fields.Datetime.now, tracking=True)

  state = fields.Selection(
    [('draft', 'Yêu cầu Báo giá (RFQ)'), ('confirmed', 'Đã Đặt Hàng (PO)'), ('done', 'Hoàn Thành'),
      ('cancel', 'Đã Hủy')], string='Trạng thái', default='draft', tracking=True)

  order_line_ids = fields.One2many('sm.purchase.order.line', 'order_id', string='Chi tiết đơn')

  picking_ids = fields.One2many('sm.stock.picking', 'purchase_id', string='Phiếu Nhập Liên Quan')
  picking_count = fields.Integer(string='Đếm Phiếu Nhập', compute='_compute_picking_count')

  total_amount = fields.Float(string='Tổng tiền', compute='_compute_total_amount', store=True)

  @api.depends('order_line_ids.price_subtotal')
  def _compute_total_amount(self):
    for rec in self:
      rec.total_amount = sum(rec.order_line_ids.mapped('price_subtotal'))

  @api.depends('picking_ids')
  def _compute_picking_count(self):
    for rec in self:
      rec.picking_count = len(rec.picking_ids)

  @api.model
  def create(self, vals):
    if vals.get('name', 'Mới') == 'Mới':
      vals['name'] = self.env['ir.sequence'].next_by_code('sm.purchase.order') or 'Mới'
    return super(PurchaseOrder, self).create(vals)

  def _get_vendor_and_internal_locations(self):
    vendor_loc = self.env['sm.stock.location'].search([('location_type', '=', 'vendor')], limit=1)
    if not vendor_loc:
      # Nếu chưa có kho nhà cung cấp, tạo đại 1 cái
      vendor_loc = self.env['sm.stock.location'].create({'name': 'Nhà Cung Cấp Hợp Tác', 'location_type': 'vendor', })

    internal_loc = self.env['sm.stock.location'].search([('location_type', '=', 'internal')], limit=1)
    if not internal_loc:
      internal_loc = self.env['sm.stock.location'].create({'name': 'Kho Công Ty Trụ Sở', 'location_type': 'internal', })
    return vendor_loc, internal_loc

  def action_confirm(self):
    for rec in self:
      if not rec.order_line_ids:
        raise UserError('Bạn không thể duyệt đơn mà không có sản phẩm nào.')

      # Sinh phiếu nhập kho (Receipt)
      vendor_loc, internal_loc = rec._get_vendor_and_internal_locations()

      picking = self.env['sm.stock.picking'].create(
        {'picking_type': 'in', 'location_id': vendor_loc.id, 'location_dest_id': internal_loc.id,
          'customer_name': rec.vendor_name, 'purchase_id': rec.id, })

      for line in rec.order_line_ids:
        if line.product_id:
          self.env['sm.stock.move'].create(
            {'name': f"Nhập kho {line.product_id.name} từ {rec.vendor_name}", 'product_id': line.product_id.id,
              'quantity': line.product_qty, 'picking_id': picking.id, })

      rec.state = 'confirmed'
      rec.message_post(body="Đơn hàng đã được duyệt, Phiếu Nhập Kho đã tạo tự động.")

  def action_done(self):
    for rec in self:
      if any(picking.state != 'done' for picking in rec.picking_ids):
        raise UserError('Phiếu Nhập Kho chưa Hoàn thành! Không thể đóng đơn này.')
      rec.state = 'done'

  def action_cancel(self):
    for rec in self:
      rec.state = 'cancel'
      for picking in rec.picking_ids:
        if picking.state != 'done':
          picking.action_cancel()

  def action_draft(self):
    for rec in self:
      rec.state = 'draft'

  def action_view_pickings(self):
    self.ensure_one()
    action = self.env.ref('om_sales.action_sm_stock_picking').read()[0]
    pickings = self.picking_ids
    if len(pickings) > 1:
      action['domain'] = [('id', 'in', pickings.ids)]
    elif pickings:
      action['views'] = [(self.env.ref('om_sales.view_sm_stock_picking_form').id, 'form')]
      action['res_id'] = pickings.id
    return action


class PurchaseOrderLine(models.Model):
  _name = 'sm.purchase.order.line'
  _description = 'Chi tiết Sản phẩm Mua'

  order_id = fields.Many2one('sm.purchase.order', string='Đơn Mua', required=True, ondelete='cascade')
  product_id = fields.Many2one('sm.sanpham', string='Sản phẩm', required=True)
  product_qty = fields.Integer(string='Số lượng', required=True, default=1)
  price_unit = fields.Float(string='Đơn giá nhập', required=True, default=0.0)

  price_subtotal = fields.Float(string='Thành tiền', compute='_compute_subtotal', store=True)

  lot_names = fields.Char(string='Số Serial', compute='_compute_lot_names')

  def _compute_lot_names(self):
    for line in self:
      done_pickings = line.order_id.picking_ids.filtered(lambda p: p.state == 'done' and p.picking_type == 'in')
      moves = self.env['sm.stock.move'].search(
        [('picking_id', 'in', done_pickings.ids), ('product_id', '=', line.product_id.id), ('state', '=', 'done')])
      lot_names = []
      for move in moves:
        for m_line in move.move_line_ids:
          if m_line.lot_id:
            lot_names.append(m_line.lot_id.name)
      line.lot_names = ", ".join(lot_names) if lot_names else ""

  @api.depends('product_qty', 'price_unit')
  def _compute_subtotal(self):
    for line in self:
      line.price_subtotal = line.product_qty * line.price_unit

  @api.onchange('product_id')
  def _onchange_product_id(self):
    if self.product_id:
      # Gợi ý đơn giá nhập có thể là một phần giá bán, hoặc giá gốc
      # Tạm lấy %70 giá bán làm giá nhập nếu chưa có
      self.price_unit = self.product_id.price * 0.7
