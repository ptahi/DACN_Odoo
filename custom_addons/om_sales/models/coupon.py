from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Coupon(models.Model):
    _name = 'sm.coupon'
    _description = 'Mã giảm giá'
    _inherit = ["mail.thread"]

1234234
    name = fields.Char(string='Mã giảm giá', required=True, copy=False)
    discount_type = fields.Selection([
        ('fixed', 'Số tiền cố định'),
        ('percentage', 'Phần trăm')
    ], string='Loại giảm giá', default='fixed', required=True ,  tracking=True)

    discount_value = fields.Float(string='Giá trị giảm', required=True, tracking=True)
    active = fields.Boolean(string='Kích hoạt', default=True, tracking=True)
    start_date = fields.Date(string='Ngày bắt đầu', tracking=True)
    end_date = fields.Date(string='Ngày kết thúc', tracking=True)

    usage_limit = fields.Integer(string='Giới hạn sử dụng', default=0, help="0 là không giới hạn", tracking=True)
    used_count = fields.Integer(string='Đã sử dụng', default=0, readonly=True , tracking=True)

    _sql_constraints = [('name_uniq', 'unique (name)', 'Mã giảm giá phải là duy nhất!')]

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for record in self:
            if record.discount_value < 0:
                raise ValidationError("Giá trị giảm không được nhỏ hơn 0.")
            if record.discount_type == 'percentage' and record.discount_value > 100:
                raise ValidationError("Phần trăm giảm giá không được lớn hơn 100.")