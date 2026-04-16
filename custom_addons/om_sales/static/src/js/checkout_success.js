/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CheckoutSuccess = publicWidget.Widget.extend({ //xóa giỏ hàng ở trang success
    selector: '.js-checkout-success',


    start() {
        console.log(' Checkout success page loaded');


        if (window.CartManager) {
            window.CartManager.clearCart();
            console.log(' Cart cleared');
        }

        return this._super(...arguments);
    },
});
