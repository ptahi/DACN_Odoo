import sys
import logging
import json
import requests
from odoo import models, api

_logger = logging.getLogger(__name__)

# Log Python path để chẩn đoán
_logger.warning("AI Module loaded - Python: %s", sys.executable)


class AIAssistant(models.AbstractModel):
  _name = 'ai.laptop.consultant'
  _description = 'AI Consultant for Laptops'

  @api.model
  def ask_ai(self, user_question):

    # Đọc API Key từ cấu hình Odoo (Settings -> Technical -> System Parameters)
    api_key = self.env['ir.config_parameter'].sudo().get_param('gemini.api_key')
    if not api_key:
      return "Hệ thống AI chưa được cấu hình API Key. Vui lòng vào Cài đặt Odoo -> Kỹ thuật -> Thông số Hệ thống để thêm 'gemini.api_key'."

    # Lấy tối đa 50 sản phẩm đang bán
    products = self.env['sm.sanpham'].sudo().search([('is_available', '=', True)], limit=50)
    product_context = ""
    for p in products:
      try:
        price = p.current_discounted_price if p.is_discount_active else p.price
      except Exception:
        price = p.price
      price_str = "{:,.0f} VND".format(price) if price else "Lien he"
      brand = p.brand_id.name if p.brand_id else "Khong ro"
      desc = p.description_sale or "Khong co mo ta"
      product_context += "- {} (Hang: {}, Gia: {}). Mo ta: {}\n".format(p.name, brand, price_str, desc)

    if not product_context:
      product_context = "Hien tai cua hang khong co san pham nao dang duoc bay ban."

    # Prompt dặn dò AI đóng vai nhân viên bán hàng
    full_prompt = """Ban la mot nhan vien tu van ban may tinh laptop chuyen nghiep, than thien va nhiet tinh cua cua hang.
Nhiem vu cua ban la doc yeu cau cua khach hang, va dua vao danh muc san pham cua hang dang co duoi day de tu van cho ho san pham phu hop nhat.
Chi tu van cac mau laptop co trong danh sach sau. KHONG DUOC bia hoac de xuat cac san pham khong co trong danh sach.

DANH MUC SAN PHAM KHA DUNG:
{}

Cau hoi cua khach hang: {}

Hay tra loi ngan gon, lich su, de hieu.""".format(product_context, user_question)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}

    try:
      response = requests.post(url, headers=headers, json=payload, timeout=30)
      response.raise_for_status()
      result = response.json()

      if "candidates" in result and len(result["candidates"]) > 0:
        return result["candidates"][0]["content"]["parts"][0]["text"]
      else:
        _logger.error("Loi Gemini API Response: %s", result)
        return "Không nhận được phản hồi hợp lệ từ AI."

    except requests.exceptions.RequestException as e:
      _logger.error("Loi khi goi REST API Gemini: %s", str(e))
      err_detail = str(e)
      if hasattr(e, 'response') and e.response is not None:
        try:
          err_detail += " - " + str(e.response.json())
        except:
          pass

      masked_key = api_key[:5] + "..." + api_key[-4:] if api_key and len(api_key) > 9 else "Invalid Key"
      return "Xin lỗi, lỗi kết nối Gemini API. Key đang dùng: [{}]. Chi tiết lỗi: {}".format(masked_key, err_detail)
