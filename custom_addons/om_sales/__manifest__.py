{
   "name":"Mini Sales Management",
   "author":"Pham Van Thai",
   "license":"LGPL-3",
   "version":"17.0.1.1",
   "depends": [
     'mail',
     'website',
     'sale',
     'stock',
     # 'account',

   ],
   "data":[
     "security/ir.model.access.csv",
     "reports/order_report.xml",
     "reports/stock_picking_report.xml",
     "views/customer_readonly_views.xml",
     "data/mail_template.xml",
     "data/mail_template_cancel.xml",
     "data/mail_template_shipping.xml",
     "data/mail_template_done.xml",
     "data/sequence.xml",

     "views/customer_views.xml",
     "views/donhang_views.xml",
     "views/sanpham_views.xml",
     "views/brand_views.xml",
     "views/coupon_views.xml",
     "views/cart_page.xml",
     "views/payment_method_page.xml",
     "views/payment_qr_page.xml",
     "views/checkout_page.xml",


     "views/checkout_success.xml",
     "views/product_brand_action.xml",
     "views/track_order_templates.xml",
     "views/contact_request_views.xml",
     "views/templates.xml",
     "views/stock_views.xml",
     "views/purchase_views.xml",
     "views/ai_chat_template.xml",
     "views/stock_lot_views.xml",
     "views/menu.xml",
     # "views/admin_dashboard.xml",
     "views/backend_dashboard_action.xml",


   ],
   "assets": {
        'web.assets_frontend': [
            'om_sales/static/src/css/website.css',
            'om_sales/static/src/css/checkout.css',
            'om_sales/static/src/css/ai_chat.css',
            'om_sales/static/src/js/website.js',
            'om_sales/static/src/js/ai_chat.js',
            'om_sales/static/src/js/checkout_success.js',
            'om_sales/static/src/js/cart.js',
            'om_sales/static/src/js/checkout.js',
            'om_sales/static/src/js/coupon_widget.js',
            'om_sales/static/src/css/compare.css',
            'om_sales/static/src/js/compare.js',




        ],
        'web.assets_backend': [
            'om_sales/static/src/components/dashboard/dashboard.css',
            'om_sales/static/src/components/dashboard/dashboard.js',
            'om_sales/static/src/components/dashboard/dashboard.xml',
            'om_sales/static/src/components/filters/date_filter.xml',
            'om_sales/static/src/components/filters/date_filter.js',
            'om_sales/static/src/components/kpi_cards/kpi_card.xml',
            'om_sales/static/src/components/kpi_cards/kpi_card.js',
            'om_sales/static/src/components/charts/revenue_chart.xml',
            'om_sales/static/src/components/charts/revenue_chart.js',
            'om_sales/static/src/components/charts/orders_chart.xml',
            'om_sales/static/src/components/charts/orders_chart.js',
            'om_sales/static/src/components/data_tables/top_products.xml',
            'om_sales/static/src/components/data_tables/top_products.js',
            'om_sales/static/src/components/data_tables/top_coupons.xml',
            'om_sales/static/src/components/data_tables/top_coupons.js',
        ],
    },
}