# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class CompareController(http.Controller):

    @http.route('/shop/compare', type='http', auth='public', website=True)
    def compare_products(self, p1=None, p2=None, **kw):
        """
        Trang so sánh 2 sản phẩm.
        p1, p2 là ID của sản phẩm.
        """
        if not p1 or not p2:
            return request.redirect('/shop')

        try:
            product1 = request.env['sm.sanpham'].sudo().browse(int(p1))
            product2 = request.env['sm.sanpham'].sudo().browse(int(p2))

            if not product1.exists() or not product2.exists():
                return request.redirect('/shop')

            values = {
                'p1': product1,
                'p2': product2,
            }
            return request.render('om_sales.product_comparison_page', values)
        except Exception:
            return request.redirect('/shop')
