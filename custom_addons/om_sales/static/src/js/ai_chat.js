/**
 * AI Chat Widget - Vanilla JS (Không dùng publicWidget để tránh xung đột Odoo scroll)
 */
(function () {
    'use strict';

    function initAIChatWidget() {
        var fab = document.getElementById('ai-chat-fab');
        var chatWindow = document.getElementById('ai-chat-window');
        var closeBtn = document.getElementById('ai-chat-close');
        var sendBtn = document.getElementById('ai-chat-send');
        var inputField = document.getElementById('ai-chat-input');
        var messagesDiv = document.getElementById('ai-chat-messages');

        // Nếu chưa load DOM thì thôi
        if (!fab || !chatWindow) return;

        var isProcessing = false;

        // Đóng/mở cửa sổ chat
        function toggleChat() {
            chatWindow.classList.toggle('d-none');
            if (!chatWindow.classList.contains('d-none')) {
                inputField.focus();
            }
        }

        fab.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleChat();
        });

        closeBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleChat();
        });

        // Gửi tin nhắn khi nhấn Enter
        inputField.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' || e.which === 13) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            sendMessage();
        });

        // Thêm tin nhắn vào giao diện
        function appendMessage(text, sender) {
            var msgDiv = document.createElement('div');
            msgDiv.classList.add('ai-message');

            if (sender === 'user') {
                msgDiv.classList.add('user-message');
                msgDiv.textContent = text;
            } else {
                msgDiv.classList.add('bot-message');
                // Render markdown đơn giản
                var html = text
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n/g, '<br/>');
                msgDiv.innerHTML = html;
            }

            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Gửi câu hỏi lên server
        function sendMessage() {
            if (isProcessing) return;

            var text = inputField.value.trim();
            if (!text) return;

            appendMessage(text, 'user');
            inputField.value = '';

            // Hiển thị trạng thái đang xử lý
            var typingDiv = document.createElement('div');
            typingDiv.classList.add('ai-message', 'bot-message', 'ai-typing');
            typingDiv.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Trợ lý đang soạn...';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            isProcessing = true;
            inputField.disabled = true;
            sendBtn.disabled = true;

            // Gọi AJAX theo đúng chuẩn jsonrpc của Odoo
            fetch('/ai/chat/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    id: 1,
                    params: {
                        question: text
                    }
                })
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    typingDiv.remove();
                    isProcessing = false;
                    inputField.disabled = false;
                    sendBtn.disabled = false;
                    inputField.focus();

                    var result = data.result;
                    if (result && result.error) {
                        appendMessage('Lỗi: ' + result.error, 'bot');
                    } else if (result && result.answer) {
                        appendMessage(result.answer, 'bot');
                    } else {
                        appendMessage('Xin lỗi, không nhận được phản hồi từ máy chủ.', 'bot');
                    }
                })
                .catch(function () {
                    typingDiv.remove();
                    isProcessing = false;
                    inputField.disabled = false;
                    sendBtn.disabled = false;
                    appendMessage('Xin lỗi, kết nối máy chủ thất bại. Vui lòng thử lại.', 'bot');
                });
        }
    }

    // Khởi tạo sau khi DOM load xong
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAIChatWidget);
    } else {
        initAIChatWidget();
    }
})();
