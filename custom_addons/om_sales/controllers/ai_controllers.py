from odoo import http
from odoo.http import request
import logging
123
_logger = logging.getLogger(__name__)


class AIChatController(http.Controller):

  @http.route('/ai/chat/ask', type='json', auth='public', methods=['POST'], website=True, csrf=False)
  def ask_ai(self, **kw):
    """
    Endpoint nhận câu hỏi từ AI Chat Widget frontend.
    """
    try:
      question = kw.get('question')

      if not question and request.jsonrequest:
        question = request.jsonrequest.get('question')

      if not question:
        return {'error': 'Vui lòng nhập câu hỏi.'}

      # Gọi Model AI đã định nghĩa (Hành động sudo để khách vãng lai public cũng gọi được)
      ai_assistant = request.env['ai.laptop.consultant'].sudo()
      answer = ai_assistant.ask_ai(question)

      return {'answer': answer}
    except Exception as e:
      _logger.error(f"Lỗi API Chat AI: {str(e)}")
      return {'error': 'Hệ thống đang bảo trì, vui lòng thử lại sau.'}
