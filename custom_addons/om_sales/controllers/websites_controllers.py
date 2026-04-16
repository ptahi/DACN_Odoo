import json
import re
from odoo import http
from odoo.http import request
import urllib.parse
import hashlib


class WebsiteSales(http.Controller):

  # FORM CHI TIẾT SẢN PHẨM
  # hiển thị từng sản phẩm có trong sm.sanpham
  @http.route('/product/<int:product_id>', type='http', auth='public', website=True)
  def product_detail(self, product_id):
    product = request.env['sm.sanpham'].sudo().browse(product_id)
    if not product.exists():
      return request.not_found()

    return request.render('om_sales.product_detail_page', {'product': product})

  # @http.route('/api/debug_orders', type='http', auth='public', website=False)
  # def debug_orders(self):
  #   orders = request.env['sm.shopping.cart'].sudo().search([])
  #   data = []
  #   for o in orders:
  #       data.append({
  #           'id': o.id,
  #           'name': o.name,
  #           'payment_type': getattr(o, 'payment_type', 'MISSING'),
  #           'total_price': o.total_price,
  #           'state': o.state,
  #       })
  #   return json.dumps(data)

  @http.route('/buy-now/<int:product_id>', type='http', auth='public', website=True)
  def buy_now_form(self, product_id):
    product = request.env['sm.sanpham'].sudo().browse(product_id)
    if not product.exists():
      return request.not_found()

    if product.qty_available <= 0:
      return request.redirect('/product/%s' % product.id)

    return request.render('om_sales.buy_now_page', {'product': product})

  # TRANG NHẬP THÔNG TIN NGƯỜI DÙNG

  @http.route('/buy-now/submit', type='http', auth='public', website=True, methods=['POST'])
  def buy_now_submit(self, **post):
    product_id = int(post.get('product_id'))
    product = request.env['sm.sanpham'].sudo().browse(product_id)
    total_price = product.current_discounted_price if product.exists() else 0

    request.session['pending_order'] = {'type': 'buy_now', 'product_id': product_id, 'name': post.get('name'),
                                        'phone': post.get('phone'), 'email': post.get('email'),
                                        'address': post.get('address'), 'total_price': total_price,
                                        'discount_amount': 0, 'coupon_code': False, 'applied_coupons': []}

    return request.render('om_sales.payment_method_page',
                          {'order': None, 'total_price': total_price, 'discount_amount': 0, 'final_price': total_price})

  @http.route('/order/cod', type='http', auth='public', website=True)
  def order_cod(self, **kw):
    # lấy dữ liệu từ pending_order
    data = request.session.get('pending_order')
    if not data:
      return request.redirect('/shop')

    # lấy dự liệu
    vals = {'customer_name': data['name'], 'customer_phone': data['phone'], 'customer_email': data.get('email'),
            'customer_address': data.get('address'), }

    # Step 1: Calculate subtotal for discount cap
    subtotal = 0
    Product = request.env['sm.sanpham'].sudo()
    cart_line_data = []
    # nếu mua ngay 1 san rphaamr
    if data['type'] == 'buy_now':
      product = Product.browse(data['product_id'])
      if product.exists():
        subtotal += product.current_discounted_price
        cart_line_data.append(
          {'product_id': data['product_id'], 'quantity': 1, 'price_unit': product.current_discounted_price})
    #     nếu mua từ giỏ hàng
    elif data['type'] == 'cart':
      for item in data['cart_items']:
        product = Product.browse(item['id'])
        if product.exists():
          qty = int(item.get('quantity', 1))
          subtotal += product.current_discounted_price * qty
          cart_line_data.append(
            {'product_id': item['id'], 'quantity': qty, 'price_unit': product.current_discounted_price})

    # Step 2: Create cart header (WITHOUT discount yet)
    # gán kiểu thanh toán
    vals['payment_type'] = 'cod'
    cart = request.env['sm.shopping.cart'].sudo().create(vals)

    # Step 3: Create cart lines
    # tạo chi tiết đơn hàng
    CartLine = request.env['sm.shopping.cart.line'].sudo()
    for line in cart_line_data:
      CartLine.create({'cart_id': cart.id, 'product_id': line['product_id'], 'quantity': line['quantity'],
                       'price_unit': line.get('price_unit', 0)})

    # Step 4: Áp dụng tất cả mã giảm giá (từ session hoặc URL)
    discount_amt, coupon_ids = self._apply_coupons_to_cart(data, kw, subtotal)
    if discount_amt > 0 and coupon_ids:
      cart.write({'coupon_ids': [(6, 0, coupon_ids)], 'coupon_id': coupon_ids[0], 'discount_amount': discount_amt})
    #   Many2many xóa mọi cũ lấy theo mới

    cart.action_awaiting_confirmation()

    request.session.pop('pending_order', None)

    return request.redirect('/order/success/%s' % cart.id)

  # TRANG THÔNG BÁO THÀNH CÔNG

  @http.route('/order/success/<int:order_id>', type='http', auth='public', website=True)
  def order_success(self, order_id):
    order = request.env['sm.shopping.cart'].sudo().browse(order_id)
    if not order.exists():
      return request.not_found()

    return request.render('om_sales.order_success_page', {'order': order})

  # LỌC SẢN PHẨM

  @http.route(['/shop', '/shop/page/<int:page>'], type='http', auth='public', website=True)
  def shop_page(self, page=1, brand=None, search=None, **kwargs):

    domain = [('is_available', '=', True)]

    if brand:
      domain.append(('brand_id', '=', int(brand)))

    if search:
      domain.append(('name', 'ilike', search))

    Product = request.env['sm.sanpham'].sudo()

    # =============================
    # SORT THEO GIÁ
    # =============================
    sort = kwargs.get('sort')

    order = 'id desc'
    if sort == 'price_asc':
      order = 'price asc'
    elif sort == 'price_desc':
      order = 'price desc'

    # =============================
    # PHÂN TRANG
    # =============================

    page_size = 8
    offset = (page - 1) * page_size

    total_products = Product.search_count(domain)
    products = Product.search(domain, order=order,  # QUAN TRỌNG
                              limit=page_size, offset=offset)

    pager = request.website.pager(url='/shop', total=total_products, page=page, step=page_size,
                                  url_args={'brand': brand, 'search': search, 'sort': sort,  # GIỮ SORT
                                            })

    brands = request.env['sm.brand'].sudo().search([])

    return request.render('om_sales.shop_page',
                          {'products': products, 'brands': brands, 'selected_brand': brand, 'search': search,
                           'sort': sort, 'pager': pager, })

    # TRANG LIÊN HỆ

  @http.route('/contact', type='http', auth='public', website=True)
  def contact_page(self, **kwargs):
    return request.render('om_sales.contact_page')

  # CONTACT SUBMIT (Xử lý lưu dữ liệu)

  @http.route('/contact/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
  def contact_submit(self, **post):
    # Tạo bản ghi trong bảng contact.request
    # Sử dụng .sudo() vì người dùng website (public) không có quyền ghi vào model
    request.env['contact.request'].sudo().create(
      {'name': post.get('name'), 'email': post.get('email'), 'phone': post.get('phone'), 'subject': post.get('subject'),
       'message': post.get('message'), 'state': 'new', })

    # Sau khi lưu xong, chuyển sang trang thông báo thành công
    return request.render('om_sales.contact_success_page')

  @http.route('/cart', type='http', auth='public', website=True)
  def cart_page(self, **kwargs):
    """Trang giỏ hàng"""
    return request.render('om_sales.cart_page')

  @http.route('/checkout', type='http', auth='public', website=True)
  def checkout_page(self, **kwargs):
    return request.render('om_sales.checkout_page')

  @http.route('/checkout/submit', type='http', auth='public', website=True, methods=['POST'])
  def checkout_submit(self, **post):

    cart_data = post.get('cart_data')
    if not cart_data:
      return request.redirect('/cart')

    try:
      cart_items = json.loads(cart_data)
    except Exception:
      return request.redirect('/cart')

    if not cart_items:
      return request.redirect('/cart')

    # Tinh tong tien
    total_price = 0
    lines = []  # store clear data
    Product = request.env['sm.sanpham'].sudo()

    for item in cart_items:
      product_id = int(item.get('id'))
      qty = int(item.get('quantity', 1))
      product = Product.browse(product_id)
      if product.exists():
        if product.qty_available < qty:
          return request.redirect('/cart')  # Redirect back to cart if not enough stock
        price = product.current_discounted_price * qty
        total_price += price
        lines.append({'id': product_id, 'quantity': qty})

    # 🔑 LƯU SESSION – CHƯA TẠO ĐƠN
    request.session['pending_order'] = {'type': 'cart', 'name': post.get('name'), 'phone': post.get('phone'),
                                        'email': post.get('email'), 'address': post.get('address'), 'cart_items': lines,
                                        'total_price': total_price, 'discount_amount': 0, 'coupon_code': False,
                                        'applied_coupons': []}

    # 👉 CHUYỂN SANG CHỌN THANH TOÁN
    return request.render('om_sales.payment_method_page',
                          {'order': None, 'total_price': total_price, 'discount_amount': 0, 'final_price': total_price})

  @http.route('/track-order', type='http', auth='public', website=True)
  def track_order_form(self, **kwargs):
    return request.render('om_sales.track_order_form', {})

  @http.route('/track-order/result', type='http', auth='public', website=True, methods=['POST'])
  def track_order_result(self, **post):
    order_code = post.get('order_code')
    phone = post.get('phone')

    order = request.env['sm.shopping.cart'].sudo().search([('name', '=', order_code), ('customer_phone', '=', phone)],
                                                          limit=1)

    values = {'order': order, 'order_code': order_code, 'phone': phone, }
    return request.render('om_sales.track_order_result', values)

  @http.route('/payment/qr/<int:order_id>', type='http', auth='public', website=True)
  def payment_qr(self, order_id):
    order = request.env['sm.shopping.cart'].sudo().browse(order_id)
    if not order.exists():
      return request.redirect('/shop')

    # ---- THÔNG TIN VIETQR ----
    bank_code = '970415'  # VietinBank
    account_no = '0868134068'
    account_name = 'PHAM VAN THAI'

    amount = int(order.total_price or 0)
    add_info = f"SM_{order.id}"

    # Encode nội dung
    # add_info = urllib.parse.quote(add_info) chuaanr bij der goi call back ngan hang
    add_info = urllib.parse.quote(order.name)

    # ---- URL VIETQR ----
    qr_url = (f"https://api.vietqr.io/image/"
              f"{bank_code}-{account_no}-print.png"
              f"?amount={amount}&addInfo={add_info}&accountName={account_name}")

    return request.render('om_sales.payment_qr_page', {'order': order, 'qr_url': qr_url, })

  def _apply_coupons_to_cart(self, data, kw, subtotal):
    """Áp dụng tất cả mã giảm giá từ session hoặc URL. Trả về (tổng_số_tiền_giảm, list_coupon_ids)."""
    from datetime import date
    today = date.today()
    Coupon = request.env['sm.coupon'].sudo()
    discount_amt = 0
    coupon_ids = []

    def get_codes_from_session():
      codes = []
      applied = data.get('applied_coupons') or []
      if applied:
        for item in applied:
          c = item.get('code') if isinstance(item, dict) else None
          if c:
            codes.append((c, item.get('discount') if isinstance(item, dict) else None))
      if not codes and data.get('coupon_code'):
        # lấy các mã phân cách bằng dấu cách phẩy xuốn òng
        for c in re.split(r'[,;\s]+', str(data['coupon_code'])):
          c = c.strip()
          if c:
            codes.append((c, None))
      return codes

    def get_codes_from_url():
      codes = []
      for key in ('coupon_codes', 'coupon_code'):
        val = kw.get(key)
        if val:
          for c in re.split(r'[,;\s]+', str(val)):
            c = c.strip()
            if c:
              codes.append((c, None))
          break
      return codes

    # tránh nhập trùng mã
    codes_with_discount = get_codes_from_session() or get_codes_from_url()
    used = set()

    for code_or_tuple in codes_with_discount:
      if isinstance(code_or_tuple, tuple):
        code, pre_discount = str(code_or_tuple[0]).strip(), code_or_tuple[1]
      else:
        code, pre_discount = str(code_or_tuple).strip(), None
      if not code or code.upper() in used:
        continue
      used.add(code.upper())
      # kiểm tra các mã với db xem tình trạng mã
      coupon = Coupon.search([('name', 'ilike', code), ('active', '=', True)], limit=1)
      if not coupon or (coupon.start_date and coupon.start_date > today) or (
          coupon.end_date and coupon.end_date < today) or (
          coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit):
        continue

      if pre_discount is not None and pre_discount > 0:
        amt = min(float(pre_discount), subtotal - discount_amt)
      else:
        if coupon.discount_type == 'fixed':
          amt = coupon.discount_value
        elif coupon.discount_type == 'percentage':
          amt = (subtotal * coupon.discount_value) / 100
        else:
          amt = 0
        amt = min(amt, subtotal - discount_amt)

      if amt > 0:
        discount_amt += amt
        coupon_ids.append(coupon.id)
        coupon.write({'used_count': coupon.used_count + 1})

    if discount_amt > subtotal:
      discount_amt = subtotal
    return discount_amt, coupon_ids

  # =========================
  # ÁP DỤNG MÃ GIẢM GIÁ (NHIỀU MÃ CÙNG LÚC)
  # =========================
  @http.route('/shop/apply_coupon', type='json', auth='public', website=True)
  def apply_coupon(self, code=None, codes=None):
    pending_order = request.session.get('pending_order')
    if not pending_order:
      return {'status': 'error', 'message': 'Không tìm thấy thông tin đơn hàng'}

    raw_codes = []
    if codes:
      raw_codes = [c.strip() for c in re.split(r'[,;\s\n]+', str(codes)) if c.strip()]
    elif code:
      raw_codes = [str(code).strip()] if str(code).strip() else []

    if not raw_codes:
      return {'status': 'error', 'message': 'Vui lòng nhập ít nhất một mã giảm giá'}

    from datetime import date
    today = date.today()
    total_price = pending_order.get('total_price', 0)
    applied = []
    total_discount = 0
    used_codes = set()

    for raw in raw_codes:
      code_upper = raw.upper().strip()
      if code_upper in used_codes:
        continue
      used_codes.add(code_upper)

      coupon = request.env['sm.coupon'].sudo().search([('name', 'ilike', code_upper), ('active', '=', True)], limit=1)
      if not coupon or (coupon.start_date and coupon.start_date > today) or (
          coupon.end_date and coupon.end_date < today) or (
          coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit):
        continue

      discount = 0
      if coupon.discount_type == 'fixed':
        discount = coupon.discount_value
        discount_label = f'-{int(discount):,}đ'
      elif coupon.discount_type == 'percentage':
        discount = (total_price * coupon.discount_value) / 100
        discount_label = f'{int(coupon.discount_value)}% (-{int(discount):,}đ)'

      if discount > 0:
        applied.append({'code': coupon.name, 'discount': discount, 'discount_label': discount_label})
        total_discount += discount

    if not applied:
      pending_order['discount_amount'] = 0
      pending_order['applied_coupons'] = []
      pending_order['coupon_code'] = False
      request.session['pending_order'] = pending_order
      request.session.modified = True
      return {'status': 'error', 'message': 'Không có mã giảm giá nào hợp lệ. Vui lòng kiểm tra lại.'}

    if total_discount > total_price:
      ratio = total_price / total_discount
      for item in applied:
        item['discount'] = round(item['discount'] * ratio, 0)
        item['discount_label'] = f'-{int(item["discount"]):,}đ'
      total_discount = total_price

    final_price = total_price - total_discount

    pending_order['discount_amount'] = total_discount
    pending_order['applied_coupons'] = applied
    pending_order['coupon_code'] = ','.join([a['code'] for a in applied])
    request.session['pending_order'] = pending_order
    request.session.modified = True

    return {'status': 'success', 'message': f'Đã áp dụng {len(applied)} mã giảm giá thành công',
      'discount_amount': total_discount, 'final_price': final_price, 'total_price': total_price,
      'applied_coupons': applied, }

  # =========================
  # KHÁCH XÁC NHẬN ĐÃ THANH TOÁN (Trang Thanks)
  # =========================
  @http.route('/payment/confirm/<int:order_id>', type='http', auth='public', website=True)
  def payment_confirm(self, order_id):
    order = request.env['sm.shopping.cart'].sudo().browse(order_id)
    if not order.exists():
      return request.redirect('/shop')

    # XÁC NHẬN ĐƠN (KHÔNG THÊM TRẠNG THÁI THANH TOÁN)
    order.action_confirm()



    return request.redirect('/order/success/%s' % order.id)

  # =========================
  # TẠO ORDER TỪ SESSION → QR
  # =========================
  @http.route('/order/qr', type='http', auth='public', website=True)
  def order_qr(self, **kw):
    data = request.session.get('pending_order')
    if not data:
      return request.redirect('/shop')

    vals = {'customer_name': data['name'], 'customer_phone': data['phone'], 'customer_email': data.get('email'),
            'customer_address': data.get('address'), }

    # Step 1: Calculate subtotal for discount cap
    subtotal = 0
    Product = request.env['sm.sanpham'].sudo()
    cart_line_data = []

    if data['type'] == 'buy_now':
      product = Product.browse(data['product_id'])
      if product.exists():
        subtotal += product.current_discounted_price
        cart_line_data.append(
          {'product_id': data['product_id'], 'quantity': 1, 'price_unit': product.current_discounted_price})
    elif data['type'] == 'cart':
      for item in data['cart_items']:
        product = Product.browse(item['id'])
        if product.exists():
          qty = int(item.get('quantity', 1))
          subtotal += product.current_discounted_price * qty
          cart_line_data.append(
            {'product_id': item['id'], 'quantity': qty, 'price_unit': product.current_discounted_price})

    # Step 2: Create cart header (WITHOUT discount yet)
    vals['payment_type'] = 'bank_transfer'
    cart = request.env['sm.shopping.cart'].sudo().create(vals)

    # Step 3: Create cart lines
    CartLine = request.env['sm.shopping.cart.line'].sudo()
    for line in cart_line_data:
      CartLine.create({'cart_id': cart.id, 'product_id': line['product_id'], 'quantity': line['quantity'],
                       'price_unit': line.get('price_unit', 0)})

    # Step 4: Áp dụng tất cả mã giảm giá (từ session hoặc URL)
    discount_amt, coupon_ids = self._apply_coupons_to_cart(data, kw, subtotal)
    if discount_amt > 0 and coupon_ids:
      cart.write({'coupon_ids': [(6, 0, coupon_ids)], 'coupon_id': coupon_ids[0], 'discount_amount': discount_amt})

    request.session.pop('pending_order', None)

    return request.redirect('/payment/qr/%s' % cart.id)

