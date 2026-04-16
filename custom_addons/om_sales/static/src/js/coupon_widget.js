/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.CouponWidget = publicWidget.Widget.extend({
    selector: '.o_coupon_section',
    events: {
        'click #btn_apply_coupon': '_onApplyCoupon',
        'click .o_btn_payment_cod': '_onPaymentClick',
        'click .o_btn_payment_qr': '_onPaymentClick',
    },

    init: function () {
        this._super.apply(this, arguments);
        this.appliedCoupons = [];
    },

    start: function () {
        $(document).on('click', '.o_btn_payment_cod, .o_btn_payment_qr', this._onPaymentClick.bind(this));
        return this._super.apply(this, arguments);
    },

    destroy: function () {
        $(document).off('click', '.o_btn_payment_cod, .o_btn_payment_qr', this._onPaymentClick.bind(this));
        this._super.apply(this, arguments);
    },

    _onPaymentClick: function (ev) {
        ev.preventDefault();
        const $target = $(ev.currentTarget);
        let url = $target.data('url');
        if (url && this.appliedCoupons && this.appliedCoupons.length > 0) {
            const codes = this.appliedCoupons.map(function (c) { return c.code; }).join(',');
            url += (url.indexOf('?') >= 0 ? '&' : '?') + 'coupon_codes=' + encodeURIComponent(codes);
        }
        if (url) {
            window.location.href = url;
        }
    },

    _renderAppliedCoupons: function (appliedCoupons, totalDiscount) {
        const $list = this.$('#applied_coupons_list');
        const $items = this.$('#applied_coupons_items');
        const $total = this.$('#applied_total_discount');
        if (!appliedCoupons || appliedCoupons.length === 0) {
            $list.hide();
            return;
        }
        $items.empty();
        appliedCoupons.forEach(function (item) {
            $items.append(
                '<li class="py-1">' +
                '<span class="badge bg-success me-2">' + item.code + '</span>' +
                '<span>' + item.discount_label + '</span>' +
                '</li>'
            );
        });
        $total.text(new Intl.NumberFormat('vi-VN').format(totalDiscount) + ' VND');
        $list.show();
    },

    _onApplyCoupon: async function (ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const $input = this.$('#coupon_code');
        const $msg = this.$('#coupon_message');
        const codes = $input.val().trim();

        if (!codes) {
            $msg.html('<span class="text-danger">Vui lòng nhập ít nhất một mã giảm giá</span>');
            return;
        }

        $btn.prop('disabled', true).text('Đang xử lý...');
        $msg.empty();

        try {
            const result = await jsonrpc('/shop/apply_coupon', {
                codes: codes,
            });

            if (result.status === 'success') {
                $('#display_discount').text(new Intl.NumberFormat('vi-VN').format(result.discount_amount) + ' VND');
                $('#display_total').text(new Intl.NumberFormat('vi-VN').format(result.final_price) + ' VND');
                $msg.html('<span class="text-success fw-bold">' + result.message + '</span>');

                this.appliedCoupons = result.applied_coupons || [];
                this._renderAppliedCoupons(this.appliedCoupons, result.discount_amount);
            } else {
                $msg.html('<span class="text-danger">' + result.message + '</span>');
                this.appliedCoupons = [];
                this._renderAppliedCoupons([], 0);
            }
        } catch (error) {
            console.error("Coupon Error:", error);
            $msg.html('<span class="text-danger">Có lỗi xảy ra. Vui lòng thử lại.</span>');
        } finally {
            $btn.prop('disabled', false).text('Áp dụng');
        }
    },
});

export default publicWidget.registry.CouponWidget;
