/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductCompare = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .js-add-to-compare': '_onAddCompare',
        'click .remove-item': '_onRemoveItem',
        'click #btn-clear-compare': '_onClearAll',
        'click #btn-compare-now': '_onCompareNow',
    },

    init: function () {
        this._super.apply(this, arguments);
        this.compareList = JSON.parse(localStorage.getItem('product_compare_list') || '[]');
    },

    start: function () {
        this._updateBar();
        return this._super.apply(this, arguments);
    },

    _onAddCompare: function (ev) {
        var $btn = $(ev.currentTarget);
        var product = {
            id: $btn.data('product-id'),
            name: $btn.data('product-name'),
            image: $btn.data('product-image')
        };

        // Check if already in list
        var index = this.compareList.findIndex(p => p.id === product.id);
        if (index !== -1) {
            this.compareList.splice(index, 1);
            $btn.removeClass('btn-info text-white').addClass('btn-outline-info');
        } else {
            if (this.compareList.length >= 2) {
                alert("Bạn chỉ có thể so sánh tối đa 2 sản phẩm.");
                return;
            }
            this.compareList.push(product);
            $btn.removeClass('btn-outline-info').addClass('btn-info text-white');
        }

        this._saveAndRefresh();
    },

    _onRemoveItem: function (ev) {
        var id = $(ev.currentTarget).data('product-id');
        this.compareList = this.compareList.filter(p => p.id !== id);
        this._saveAndRefresh();
    },

    _onClearAll: function () {
        this.compareList = [];
        this._saveAndRefresh();
    },

    _onCompareNow: function () {
        if (this.compareList.length === 2) {
            window.location.href = '/shop/compare?p1=' + this.compareList[0].id + '&p2=' + this.compareList[1].id;
        }
    },

    _saveAndRefresh: function () {
        localStorage.setItem('product_compare_list', JSON.stringify(this.compareList));
        this._updateBar();
    },

    _updateBar: function () {
        var $bar = $('#comparison-bar');
        var $items = $('#comparison-items');
        var $btn = $('#btn-compare-now');

        if (this.compareList.length > 0) {
            $bar.removeClass('d-none');
            $items.empty();

            this.compareList.forEach(p => {
                var html = `
                    <div class="d-flex align-items-center gap-2">
                        <div class="comparison-item">
                            <img src="${p.image}" alt="${p.name}"/>
                            <span class="remove-item" data-product-id="${p.id}">&times;</span>
                        </div>
                        <span class="comparison-item-name text-white d-none d-lg-inline">${p.name}</span>
                    </div>
                `;
                $items.append(html);
            });

            if (this.compareList.length === 2) {
                $btn.prop('disabled', false).removeClass('btn-secondary').addClass('btn-primary');
            } else {
                $btn.prop('disabled', true).removeClass('btn-primary').addClass('btn-secondary');
            }
        } else {
            $bar.addClass('d-none');
        }

        // Highlight selected buttons on page load/change
        $('.js-add-to-compare').each((i, el) => {
            var id = $(el).data('product-id');
            if (this.compareList.some(p => p.id === id)) {
                $(el).removeClass('btn-outline-info').addClass('btn-info text-white');
            } else {
                $(el).removeClass('btn-info text-white').addClass('btn-outline-info');
            }
        });
    }
});

export default publicWidget.registry.ProductCompare;
