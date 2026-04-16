/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CheckoutPage = publicWidget.Widget.extend({
    selector: '.checkout-page',

    events: {
        'submit form': '_onSubmit',
    },

    start() {
        console.log('✅ CheckoutPage mounted');
        this._renderCart();
        return this._super(...arguments);
    },

    // =============================
    // RENDER CART
    // =============================
    _renderCart() {
        const CartManager = window.CartManager;
        const cart = CartManager.getCart();

        const $body = this.$('#checkout-cart-body');
        const $total = this.$('#checkout-total');


        if (!cart || !cart.length) {
            $body.html('<tr><td colspan="3" class="text-danger">Giỏ hàng trống</td></tr>');
            $total.text('0 ₫');
            return;
        }

        let html = '';
        let total = 0;

        cart.forEach(item => {
            const lineTotal = item.price * item.quantity;
            total += lineTotal;

            html += `
                <tr>
                    <td>${item.name}</td>
                    <td class="text-center">${item.quantity}</td>
                    <td class="text-end">${lineTotal.toLocaleString()} ₫</td>
                </tr>
            `;
        });

        $body.html(html);
        $total.text(total.toLocaleString() + ' ₫');

        // Hiện bảng
        this.$('#checkout-cart').removeClass('d-none');
    },


    // =============================
    // SUBMIT ĐƠN HÀNG
    // =============================
    _onSubmit(ev) {
        ev.preventDefault();

        const CartManager = window.CartManager;
        const cart = CartManager.getCart();

        if (!cart.length) {
            alert('Giỏ hàng trống');
            return;
        }

        const form = ev.currentTarget;

        // 🔥 QUAN TRỌNG: đẩy cart vào hidden input
        const cartInput = form.querySelector('input[name="cart_data"]');
        cartInput.value = JSON.stringify(cart);

        // ✅ submit form bình thường để backend nhận
        form.submit();

        // ❌ KHÔNG clear cart ở đây
        // → clear sau khi backend tạo đơn thành công

    },
});
