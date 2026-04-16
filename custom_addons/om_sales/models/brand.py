from odoo import api, fields, models

class Brand(models.Model):
    _name = 'sm.brand'
    _description = 'Hãng sản phẩm'
    _inherit = ["mail.thread"]
    name = fields.Char(string='Tên hãng',
                       required=True,)
    code = fields.Char(string='Mã hãng',
                       )
    active = fields.Boolean(default=True)
