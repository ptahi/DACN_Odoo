/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

// ============================================
// CART MANAGER - Quản lý localStorage
// ============================================
const CartManager = {
    STORAGE_KEY: 'odoo_cart',// Định nghĩa tên key để lưu trong localStorage của trình duyệt

    getCart() {
        const cart = localStorage.getItem(this.STORAGE_KEY);
        return cart ? JSON.parse(cart) : [];
    },

    saveCart(cart) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateCartBadge();
    },

    addItem(product) {
        const cart = this.getCart(); //Lấy dữ liệu từ browser, chuyển từ chuỗi JSON sang mảng Object.
        const existingItem = cart.find(item => item.id === product.id);

        if (existingItem) {
            existingItem.quantity += 1; // nếu có rồi tăng thêm 1
        } else {
            cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                image: product.image,
                quantity: 1
            });
        }

        this.saveCart(cart);
        return cart;
    },

    updateQuantity(productId, quantity) {
        const cart = this.getCart();
        const item = cart.find(item => item.id === productId);

        if (item) {
            item.quantity = Math.max(1, parseInt(quantity));
            this.saveCart(cart);
        }

        return cart;
    },

    removeItem(productId) {
        let cart = this.getCart();
        cart = cart.filter(item => item.id !== productId);
        this.saveCart(cart);
        return cart;
    },

    clearCart() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateCartBadge();
    },

    getTotalItems() {
        const cart = this.getCart();
        return cart.reduce((total, item) => total + item.quantity, 0);
    },

    getTotalPrice() {
        const cart = this.getCart();
        return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    },

    updateCartBadge() {
        const totalItems = this.getTotalItems();
        const badge = document.querySelector('.js-cart-count');

        if (badge) {
            if (totalItems > 0) {
                badge.textContent = totalItems;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    },

    formatPrice(price) {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    }
};
window.CartManager = CartManager;

// ============================================
// WIDGET - Nút Thêm vào giỏ
// ============================================
publicWidget.registry.AddToCartButton = publicWidget.Widget.extend({
    selector: '.js-add-to-cart', // định danh nút bấm trong templates
    events: {
        'click': '_onAddToCart', // Khi click vào nút, chạy hàm _onAddToCart
    },

    start() {
        CartManager.updateCartBadge();
        return this._super(...arguments);
    },

    async _onAddToCart(ev) { // event thêm giỏ hàng Đọc thông tin sản phẩm từ các thuộc tính data-* (data-product-id, data-product-name,...) được gắn trên thẻ HTML của nút.
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const productData = {
            id: parseInt($btn.data('product-id')),
            name: $btn.data('product-name'),
            price: parseFloat($btn.data('product-price')),
            image: $btn.data('product-image')
        };


        // Animation
        const originalText = $btn.html();
        $btn.prop('disabled', true)
            .html('<i class="fa fa-spinner fa-spin"></i> Đang thêm...');

        // Thêm vào giỏ
        setTimeout(() => {
            CartManager.addItem(productData);

            // Success feedback
            $btn.html('<i class="fa fa-check"></i> Đã thêm!')
                .removeClass('btn-primary')
                .addClass('btn-success');

            setTimeout(() => {
                $btn.html(originalText)
                    .removeClass('btn-success')
                    .addClass('btn-primary')
                    .prop('disabled', false);
            }, 300);

            // Show notification
            this._showNotification(productData.name);
        }, 300);
    },

    _showNotification(productName) {
        // Toast notification (nếu có Bootstrap 5 toast)
        const message = `"${productName}" đã được thêm vào giỏ hàng!`;

        // Simple alert (có thể thay bằng toast đẹp hơn)
        if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification('Thêm vào giỏ hàng', {
                body: message,
                icon: '/web/static/src/img/favicon.ico'
            });
        } else {
            // Fallback: console log hoặc custom notification
            console.log(message);
        }
    }
});


// ============================================
// WIDGET - Trang giỏ hàng
// ============================================
publicWidget.registry.CartPage = publicWidget.Widget.extend({
    selector: '.js-cart-page',
    events: {
        'click .js-qty-plus': '_onQuantityPlus',
        'click .js-qty-minus': '_onQuantityMinus',
        'change .js-qty-input': '_onQuantityChange',
        'click .js-remove-item': '_onRemoveItem',
        'click .js-clear-cart': '_onClearCart',
    },

    start() {
        this._renderCart();
        CartManager.updateCartBadge();
        return this._super(...arguments);
    },

    _renderCart() {
        const cart = CartManager.getCart();
        const $emptyState = this.$('#cart-empty');
        const $cartContent = this.$('#cart-content');
        const $cartBody = this.$('#cart-body');

        if (cart.length === 0) {
            $emptyState.show();
            $cartContent.hide();
            return;
        }

        $emptyState.hide();
        $cartContent.show();
        $cartBody.empty();

        cart.forEach(item => {
            const $row = this._createCartRow(item);
            $cartBody.append($row);
        });

        this._updateTotals();
    },

    _createCartRow(item) {
        const $row = $(`
            <tr class="cart-line" data-product-id="${item.id}">
                <td>
                    <div class="d-flex align-items-center">
                        <img src="${item.image}" alt="${item.name}"
                             class="me-3 rounded"
                             style="width: 80px; height: 80px; object-fit: cover;"
                             onerror="this.src='/web/static/src/img/placeholder.png'"/>
                        <div>
                            <h6 class="mb-0">${item.name}</h6>
                            <small class="text-muted">Mã SP: ${item.id}</small>
                        </div>
                    </div>
                </td>
                <td class="text-center">
                    <div class="input-group d-inline-flex" style="width: 160px;">
                        <button class="btn btn-outline-secondary js-qty-minus" type="button">
                            <i class="fa fa-minus"></i>
                        </button>
                        <input type="number"
                               class="form-control text-center js-qty-input"
                               style="min-width: 60px;"
                               value="${item.quantity}"
                               min="1"/>
                        <button class="btn btn-outline-secondary js-qty-plus" type="button">
                            <i class="fa fa-plus"></i>
                        </button>
                    </div>
                </td>
                <td class="text-end">
                    <div>${CartManager.formatPrice(item.price)}</div>
                    <small class="text-muted">× ${item.quantity}</small>
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-sm btn-outline-danger js-remove-item">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            </tr>
        `);

        return $row;
    },

    _updateTotals() {
        const total = CartManager.getTotalPrice();
        this.$('#cart-subtotal').text(CartManager.formatPrice(total));
        this.$('#cart-total').text(CartManager.formatPrice(total));
    },

    _onQuantityPlus(ev) {
        const $row = $(ev.currentTarget).closest('.cart-line');
        const $input = $row.find('.js-qty-input');
        const newQty = parseInt($input.val()) + 1;
        $input.val(newQty);
        this._updateItemQuantity($row, newQty);
    },

    _onQuantityMinus(ev) {
        const $row = $(ev.currentTarget).closest('.cart-line');
        const $input = $row.find('.js-qty-input');
        const newQty = Math.max(1, parseInt($input.val()) - 1);
        $input.val(newQty);
        this._updateItemQuantity($row, newQty);
    },

    _onQuantityChange(ev) {
        const $row = $(ev.currentTarget).closest('.cart-line');
        const newQty = Math.max(1, parseInt($(ev.currentTarget).val()) || 1);
        this._updateItemQuantity($row, newQty);
    },

    _updateItemQuantity($row, quantity) {
        const productId = parseInt($row.data('product-id'));
        CartManager.updateQuantity(productId, quantity);
        this._renderCart();
    },

    _onRemoveItem(ev) {
        const $row = $(ev.currentTarget).closest('.cart-line');
        const productId = parseInt($row.data('product-id'));

        if (confirm('Bạn có chắc muốn xóa sản phẩm này?')) {
            CartManager.removeItem(productId);
            this._renderCart();
        }
    },

    _onClearCart(ev) {
        if (confirm('Bạn có chắc muốn xóa toàn bộ giỏ hàng?')) {
            CartManager.clearCart();
            this._renderCart();
        }
    }
});


// ============================================
// Khởi tạo khi page load
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    CartManager.updateCartBadge();
});