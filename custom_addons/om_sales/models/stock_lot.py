from odoo import models, fields, api


class StockLot(models.Model):
  _name = 'sm.stock.lot'
  _description = 'Lô / Số Serial'
  _order = 'create_date desc'

  name = fields.Char(string='Số Serial / Lô', required=True, index=True)
  product_id = fields.Many2one('sm.sanpham', string='Sản phẩm', required=True)
  note = fields.Text(string='Ghi chú (Bảo hành, Quy cách...)')
  current_location_id = fields.Many2one('sm.stock.location', string='Vị trí hiện tại')
  company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)

  mfg_date = fields.Date(string='Ngày sản xuất/Ngày nhập')
  warranty_end_date = fields.Date(string='Hạn bảo hành')
  warranty_status = fields.Selection(
    [('in_warranty', 'Còn Bảo Hành'), ('out_of_warranty', 'Hết Bảo Hành'), ('none', 'Chưa có thông tin')],
    string='Trạng thái bảo hành', compute='_compute_warranty_status', store=True)

  @api.depends('warranty_end_date')
  def _compute_warranty_status(self):
    today = fields.Date.today()
    for lot in self:
      if not lot.warranty_end_date:
        lot.warranty_status = 'none'
      elif lot.warranty_end_date >= today:
        lot.warranty_status = 'in_warranty'
      else:
        lot.warranty_status = 'out_of_warranty'

  _sql_constraints = [('name_uniq', 'unique (name)',
                       'Số Serial này đã tồn tại trong hệ thống! Mỗi Số Serial phải là duy nhất trên toàn bộ sản phẩm.')]

  move_line_ids = fields.One2many('sm.stock.move.line', 'lot_id', string='Lịch sử dịch chuyển')
  move_count = fields.Integer(string='Lịch sử', compute='_compute_move_count')

  def _compute_move_count(self):
    for lot in self:
      lot.move_count = len(lot.move_line_ids)

  def action_view_moves(self):
    self.ensure_one()
    action = self.env.ref('om_sales.action_sm_stock_move').read()[0]
    action['domain'] = [('lot_id', '=', self.id)]
    action['context'] = {'default_lot_id': self.id}
    return action


class StockMoveLine(models.Model):
  _name = 'sm.stock.move.line'
  _description = 'Chi tiết Số Serial Dịch chuyển'

  move_id = fields.Many2one('sm.stock.move', string='Lịch sử dịch chuyển (Move)', required=True, ondelete='cascade')
  picking_id = fields.Many2one('sm.stock.picking', related='move_id.picking_id', store=True, string='Phiếu Kho')

  product_id = fields.Many2one('sm.sanpham', related='move_id.product_id', store=True, string='Sản phẩm')
  lot_id = fields.Many2one('sm.stock.lot', string='Số Serial/Lô')
  lot_name = fields.Char(string='Tạo Số Serial Mới')

  qty_done = fields.Float(string='Hoàn thành', default=1.0)

  location_id = fields.Many2one('sm.stock.location', related='move_id.location_id', store=True, string='Từ vị trí')
  location_dest_id = fields.Many2one('sm.stock.location', related='move_id.location_dest_id', store=True,
                                     string='Tới vị trí')

  state = fields.Selection(related='move_id.state', store=True, readonly=False, string='Trạng thái')

  @api.onchange('lot_id')
  def _onchange_lot_id(self):
    if self.lot_id and self.lot_id.product_id != self.product_id:
      return {'warning': {'title': 'Cảnh báo', 'message': 'Số Serial này thuộc về một Sản Phẩm khác!'}}
