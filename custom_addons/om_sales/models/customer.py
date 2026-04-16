from odoo import api, fields, models


class Customer(models.Model):
    _name = 'sm.customer'
    _description = 'Customer'
    _inherit = ["mail.thread"]
    name = fields.Char(
        string='Customer Name',
        required=True,
        tracking=True,
    )

    phone = fields.Char(
        string='Phone Number',
        tracking = True,
    )

    email = fields.Char(
        string='Email',
        tracking=True,
    )

    address = fields.Text(
        string='Address',
        tracking=True,
    )

    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        string='Gender',
        tracking=True,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )
