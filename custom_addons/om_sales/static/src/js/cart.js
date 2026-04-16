/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
//const CartManager = require('sm_shop.website');

publicWidget.registry.CartCheckoutOnly = publicWidget.Widget.extend({
    selector: '.js-cart-page',

    events: {
        'click .btn-checkout': '_onCheckout',
    },

    start() {
        console.log('✅ CartCheckoutOnly mounted');
        return this._super(...arguments);
    },

    _onCheckout() {
        console.log('👉 Checkout click');

        const cart = CartManager.getCart();

        // Chỉ kiểm tra – KHÔNG sửa – KHÔNG render
        if (!Array.isArray(cart) || cart.length === 0) {
            alert('Giỏ hàng trống');
            return;
        }

        fetch('/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cart }),
        }).then(() => {
            window.location.href = '/checkout';
        });
    },
});
