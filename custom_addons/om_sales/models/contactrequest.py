from odoo import models, fields, api

class ContactRequest(models.Model):
    _name = 'contact.request'
    _description = 'Yêu cầu liên hệ'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Họ tên', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Số điện thoại', tracking=True)
    subject = fields.Char(string='Tiêu đề', tracking=True)
    message = fields.Text(string='Nội dung')
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_consultation', 'Đang tư vấn'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Hủy bỏ')
    ], string='Trạng thái', default='new', tracking=True)

    def action_in_consultation(self):
        for record in self:
            record.state = 'in_consultation'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'