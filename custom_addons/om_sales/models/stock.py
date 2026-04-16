from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockLocation(models.Model):
  _name = 'sm.stock.location'
  _description = 'Vị trí Kho'

  name = fields.Char(string='Tên vị trí', required=True)
  location_type = fields.Selection(
    [('internal', 'Kho Nội Bộ'), ('customer', 'Kho Khách Hàng'), ('vendor', 'Kho Nhà Cung Cấp'),
      ('loss', 'Kho Hư Hỏng / Mất Mát')], string='Loại vị trí', default='internal', required=True)
  active = fields.Boolean(default=True)
  company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)


class StockPicking(models.Model):
  _name = 'sm.stock.picking'
  _description = 'Phiếu Kho'
  _order = 'id desc'

  name = fields.Char(string='Mã phiếu', default='Mới', copy=False, readonly=True)
  picking_type = fields.Selection([('in', 'Nhập Kho'), ('out', 'Xuất Kho'), ('internal', 'Chuyển Nội Bộ')],
    string='Loại phiếu', required=True)

  state = fields.Selection([('draft', 'Nháp'), ('ready', 'Chờ xử lý'), ('done', 'Hoàn thành'), ('cancel', 'Đã Hủy')],
    string='Trạng thái', default='draft')

  location_id = fields.Many2one('sm.stock.location', string='Từ vị trí (Nguồn)', required=True)
  location_dest_id = fields.Many2one('sm.stock.location', string='Tới vị trí (Đích)', required=True)

  cart_id = fields.Many2one('sm.shopping.cart', string='Đơn hàng liên quan (SO/PO)')
  purchase_id = fields.Many2one('sm.purchase.order', string='Đơn Mua Hàng')
  customer_name = fields.Char(string='Khách hàng / Đối tác')

  date_done = fields.Datetime(string='Ngày hoàn thành', readonly=True)

  move_ids = fields.One2many('sm.stock.move', 'picking_id', string='Chi tiết dịch chuyển')

  @api.model
  def create(self, vals):
    if vals.get('name', 'Mới') == 'Mới':
      vals['name'] = self.env['ir.sequence'].next_by_code('sm.stock.picking') or 'Mới'
    return super(StockPicking, self).create(vals)

  def action_print_picking(self):
    self.ensure_one()
    return self.env.ref('om_sales.action_report_stock_picking').report_action(self)

  def action_confirm(self):
    for record in self:
      if not record.move_ids:
        raise UserError('Phiếu kho không có chi tiết sản phẩm.')
      record.state = 'ready'

  def action_done(self):
    for record in self:
      if record.state != 'ready':
        raise UserError('Chỉ có thể hoàn thành phiếu ở trạng thái "Chờ xử lý".')

      entered_serials = set()

      for move in record.move_ids:
        if len(move.move_line_ids) != move.quantity:
          raise UserError(
            f'Sản phẩm "{move.product_id.name}" Cần xác nhận {move.quantity} máy, nhưng mới khai báo {len(move.move_line_ids)} Serial.')

        for line in move.move_line_ids:
          # Nếu là Nhập Kho NHƯNG LẠI TỪ ĐƠN MUA HÀNG hoặc THỦ CÔNG (không phải trả hàng) -> Tạo Serial mới
          if record.picking_type == 'in' and not record.cart_id:
            if not line.lot_name:
              raise UserError(f'Phiếu Nhập: Vui lòng nhập Số Serial mới cho sản phẩm "{move.product_id.name}"')

            if line.lot_name in entered_serials:
              raise UserError(
                f'Lỗi: Số Serial "{line.lot_name}" được nhập / quét nhiều lần trong cùng một phiếu nhập! Mỗi mã Serial chỉ được xuất hiện 1 lần.')
            entered_serials.add(line.lot_name)

            # Lưu serial mới vào database (hoặc lấy nếu đã tồn tại)
            existing_lot = self.env['sm.stock.lot'].search([('name', '=', line.lot_name)], limit=1)
            if existing_lot:
              if existing_lot.product_id.id != move.product_id.id:
                raise UserError(
                  f'Phiếu Nhập: Số Serial "{line.lot_name}" đã tồn tại trong hệ thống, thuộc về sản phẩm khác ({existing_lot.product_id.name}). Mỗi Serial chỉ được tồn tại duy nhất 1 lần!')
              line.lot_id = existing_lot.id
            else:
              new_lot = self.env['sm.stock.lot'].create({'name': line.lot_name, 'product_id': move.product_id.id,
                'company_id': record.company_id.id if hasattr(record,
                                                              'company_id') and record.company_id else self.env.company.id})
              line.lot_id = new_lot.id
          else:
            # Phiếu Xuất, Nội bộ, HOẶC Phiếu Khách trả hàng -> Yêu cầu CHỌN Serial đã có sẵn
            if not line.lot_id:
              action_name = "Phiếu Xuất/Trả hàng"
              raise UserError(
                f'{action_name}: Vui lòng CHỌN Số Serial đang có sẵn cho sản phẩm "{move.product_id.name}"')

            if line.lot_id.name in entered_serials:
              raise UserError(
                f'Lỗi: Số Serial "{line.lot_id.name}" được chọn nhiều lần trong cùng một phiếu! Mỗi mã Serial chỉ được xuất hiện 1 lần.')

            # Kiểm tra vị trí hiện tại của Serial xem có khớp với Kho Nguồn không
            if line.lot_id.current_location_id and line.lot_id.current_location_id.id != record.location_id.id:
              raise UserError(
                f'Lỗi: Số Serial "{line.lot_id.name}" hiện đang nằm ở "{line.lot_id.current_location_id.name}", không có ở kho xuất "{record.location_id.name}". Bạn không thể chọn máy này!')

            # Kiểm tra Khách trả hàng: Serial phải nằm trong các mã đã giao của đơn hàng
            if record.picking_type == 'in' and record.cart_id:
              out_pickings = record.cart_id.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type == 'out')
              shipped_count = self.env['sm.stock.move.line'].search_count(
                [('picking_id', 'in', out_pickings.ids), ('lot_id', '=', line.lot_id.id), ('state', '=', 'done')])
              if shipped_count == 0:
                raise UserError(
                  f'Lỗi: Số Serial "{line.lot_id.name}" không thuộc về đơn hàng {record.cart_id.name} đã giao trước đó! Bạn chỉ được chọn Số Serial khớp với máy đã bán.')

            entered_serials.add(line.lot_id.name)

          # Cập nhật vị trí hiện tại của Serial ngay khi hoàn thành di chuyển
          if line.lot_id:
            line.lot_id.current_location_id = record.location_dest_id.id

        move.move_line_ids.write({'state': 'done'})

        move.state = 'done'
      record.state = 'done'
      record.date_done = fields.Datetime.now()

      # Kiểm tra Quy tắc Cung ứng (Auto PO) nếu là phiếu Xuất hoặc Nội bộ
      if record.picking_type in ('out', 'internal'):
        for move in record.move_ids:
          # Gọi hàm kiểm tra cung ứng trên class sản phẩm
          move.product_id.action_check_reordering_rules()

  def action_cancel(self):
    for record in self:
      for move in record.move_ids:
        move.state = 'cancel'
      record.state = 'cancel'


class StockMove(models.Model):
  _name = 'sm.stock.move'
  _description = 'Chi tiết Dịch chuyển Kho'

  name = fields.Char(string='Mô tả', required=True)
  product_id = fields.Many2one('sm.sanpham', string='Sản phẩm', required=True)
  quantity = fields.Integer(string='Số lượng', default=1, required=True)

  location_id = fields.Many2one('sm.stock.location', string='Nguồn', related='picking_id.location_id', store=True)
  location_dest_id = fields.Many2one('sm.stock.location', string='Đích', related='picking_id.location_dest_id',
                                     store=True)

  picking_id = fields.Many2one('sm.stock.picking', string='Phiếu kho', required=True, ondelete='cascade')
  picking_type = fields.Selection(related='picking_id.picking_type')
  cart_id = fields.Many2one('sm.shopping.cart', related='picking_id.cart_id', string='Đơn bán hàng')

  move_line_ids = fields.One2many('sm.stock.move.line', 'move_id', string='Chi tiết Serial')

  lot_names = fields.Char(string='Số Serial đã chọn', compute='_compute_lot_names')

  @api.depends('move_line_ids.lot_id', 'move_line_ids.lot_name')
  def _compute_lot_names(self):
    for move in self:
      names = []
      for line in move.move_line_ids:
        if line.lot_id:
          names.append(line.lot_id.name)
        elif line.lot_name:
          names.append(line.lot_name)
      move.lot_names = ", ".join(names) if names else ""

  state = fields.Selection([('draft', 'Nháp'), ('ready', 'Chờ xử lý'), ('done', 'Thành công'), ('cancel', 'Đã Hủy')],
    string='Trạng thái', default='draft')

  def action_show_details(self):
    self.ensure_one()
    view = self.env.ref('om_sales.view_sm_stock_move_operations')
    return {'name': f'Chi tiết Số Serial: {self.product_id.name}', 'type': 'ir.actions.act_window', 'view_mode': 'form',
      'res_model': 'sm.stock.move', 'views': [(view.id, 'form')], 'view_id': view.id, 'target': 'new',
      'res_id': self.id,
      'context': dict(self.env.context, default_move_id=self.id, default_product_id=self.product_id.id,
        default_location_id=self.location_id.id, default_location_dest_id=self.location_dest_id.id,
        default_picking_type=self.picking_id.picking_type, )}
