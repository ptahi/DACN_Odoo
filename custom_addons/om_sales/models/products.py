from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Sanpham(models.Model):
  _name = 'sm.sanpham'
  _description = 'SanPham'
  _inherit = ["mail.thread"]

  name = fields.Char(string='Tên sản phẩm', required=True, translate=True, tracking=True)
  brand_id = fields.Many2one('sm.brand', string='Hãng', ondelete='restrict', tracking=True)

  code = fields.Char(string='Mã sản phẩm', required=True, index=True, tracking=True, copy=False)

  description_sale = fields.Text(string='Mô tả bán hàng', translate=True, tracking=True)
  note = fields.Text(string='Ghi chú')
  price = fields.Float(string='Gía Bán')
  image_1920 = fields.Image(string="Hình ảnh sản phẩm", max_width=1920, max_height=1920,
                            website=True, )  # thêm ảnh để hiển thị
  qty_available = fields.Integer(string='Tồn kho', compute='_compute_qty_available')

  barcode = fields.Char(string='Mã vạch (Barcode)', copy=False)

  def _compute_qty_available(self):
    for record in self:
      # Tính tổng nhập (dest = internal)
      incoming = self.env['sm.stock.move'].search(
        [('product_id', '=', record.id), ('state', '=', 'done'), ('location_dest_id.location_type', '=', 'internal')])

      # Tính tổng xuất (source = internal)
      outgoing = self.env['sm.stock.move'].search(
        [('product_id', '=', record.id), ('state', '=', 'done'), ('location_id.location_type', '=', 'internal')])

      qty_in = sum(incoming.mapped('quantity'))
      qty_out = sum(outgoing.mapped('quantity'))
      record.qty_available = qty_in - qty_out

  # Auto PO Rules
  min_qty = fields.Integer(string='Tồn kho tối thiểu', default=0,
                           help='Khi tồn kho dưới mức này, hệ thống sẽ đề xuất tạo đơn mua hàng')
  reorder_qty = fields.Integer(string='Số lượng đặt thêm', default=0,
                               help='Hệ thống sẽ dặt mua số lượng này khi tiến hành gom đơn')
  default_vendor_name = fields.Char(string='Tên Nhà cung cấp mặc định',
                                    help='Tên lấy làm đối tác để lên phiếu mua hàng tự động')

  def action_check_reordering_rules(self):
    """Kiểm tra điều kiện tồn kho và báo cho Mua hàng"""
    for record in self:
      if record.qty_available < record.min_qty and record.reorder_qty > 0 and record.default_vendor_name:
        # Tìm xem có RFQ nào đang nháp của nhà cung cấp này không
        draft_po = self.env['sm.purchase.order'].search(
          [('vendor_name', '=', record.default_vendor_name), ('state', '=', 'draft')], limit=1)

        if not draft_po:
          draft_po = self.env['sm.purchase.order'].create({'vendor_name': record.default_vendor_name, 'state': 'draft'})

        # Kiểm tra xem sản phẩm đã có trong PO chưa, nêú có thì cộng thêm số lượng, hoặc tạo line mới
        existing_line = draft_po.order_line_ids.filtered(lambda l: l.product_id.id == record.id)
        if existing_line:
          pass  # Đã có trong đơn nháp (hoặc nếu muốn có thể cộng dồn += record.reorder_qty nhưng ở đây pass cho an toàn)
        else:
          self.env['sm.purchase.order.line'].create(
            {'order_id': draft_po.id, 'product_id': record.id, 'product_qty': record.reorder_qty,
              'price_unit': record.price * 0.7  # Tạm gợi ý nhập = 70% giá bán
            })

        # Ghi log
        record.message_post(
          body=f"Cảnh báo: Tồn kho đã rớt xuống dưới mức tối thiểu ({record.min_qty}). Hệ thống đã tự động đưa {record.reorder_qty} sản phẩm vào Đơn Mua Hàng nháp (Mã Đơn: {draft_po.name}) cho nhà cung cấp {record.default_vendor_name}.")

  is_available = fields.Boolean(string='Còn bán', default=True, tracking=True)

  discount_percentage = fields.Float(string='Phần trăm giảm giá (%)', default=0.0)
  discount_start_date = fields.Datetime(string='Thời gian bắt đầu giảm giá')
  discount_end_date = fields.Datetime(string='Thời gian kết thúc giảm giá')

  is_discount_active = fields.Boolean(string='Đang trong thời gian khuyến mãi', compute='_compute_discount_status',
    store=False, )

  current_discounted_price = fields.Float(string='Giá sau khi giảm', compute='_compute_current_discounted_price',
    store=False, )

  @api.depends('discount_percentage', 'discount_start_date', 'discount_end_date')
  def _compute_discount_status(self):
    now = fields.Datetime.now()
    for record in self:
      if record.discount_percentage > 0 and record.discount_start_date and record.discount_end_date:
        record.is_discount_active = record.discount_start_date <= now <= record.discount_end_date
      elif record.discount_percentage > 0 and not record.discount_start_date and not record.discount_end_date:
        # If active without date range, it's just active based on percentage
        record.is_discount_active = True
      else:
        record.is_discount_active = False

  @api.depends('price', 'discount_percentage', 'is_discount_active')
  def _compute_current_discounted_price(self):
    for record in self:
      if record.is_discount_active and record.discount_percentage > 0:
        record.current_discounted_price = record.price * (1 - record.discount_percentage / 100.0)
      else:
        record.current_discounted_price = record.price

  def action_add_to_cart(self):  # add sản phẩm mới vào giỏ hàng

    self.ensure_one()  # chỉ chứa 1 bản ghi
    # current_price = self.price

    cart = self.env['sm.shopping.cart'].create({'name': 'Mới', 'cart_line_ids': [(0, 0,
                                                                                  {'product_id': self.id, 'quantity': 1,
                                                                                   'price_unit': self.current_discounted_price})]})  # thêm sản phẩm vào giỏ hàng lấy price từ bảng products

    # 'price_unit': 0, 'price': current_price,

    return {'name': 'Giỏ hàng', 'type': 'ir.actions.act_window', 'res_model': 'sm.shopping.cart', 'res_id': cart.id,

            'view_mode': 'form', 'target': 'current', }

  def action_buy_now(self):

    return self.action_add_to_cart()

