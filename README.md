# Hướng dẫn cài đặt môi trường để chạy dự án 

Làm theo các bước dưới đây để cài đặt môi trường và chạy dự án 

## Yêu cầu hệ thống:
- Docker đã được cài đặt trên máy tính

### Bước 1: Tải xuống source code của dự án
Pull/Clone hoặc tải xuống source code dự án từ gitlab

### Bước 2: Tạo file docker-compose.yml
Tạo file docker-compose.yml từ file mẫu docker-compose.example

### Bước 3: Tạo Master Password
Tạo file odoo_pg_pass từ file mẫu odoo_pg_pass_example

### Bước 4: Chạy dự án
Chạy lệnh docker compose up -d --build để chạy file docker-compose.yml được build từ Dockerfile mới nhất

### Bước 5: Truy cập vào Odoo
Mở trình duyệt và truy cập vào địa chỉ http://localhost:8069 để sử dụng (8069 là cổng mặc định của Odoo)

### Bước 6: Tạo cơ sở dữ liệu
Khi truy cập vào Odoo lần đầu tiên, bạn sẽ được yêu cầu tạo một cơ sở dữ liệu mới. Nhập thông tin cần thiết và nhấn nút "Create Database" để sử dụng
### Bước 7: Cài đặt module om_sales
Vào Apps chọn Update Apps List
Chọn Install om_sales


Để chạy chức năng AI cần phải có API Key của OpenAI, bạn có thể lấy API Key tại https://platform.openai.com/account/api-keys hoặc lấy key API có sẵn "AIzaSyBMcCtDTX32PQjbxIrbuh0NIcGLdZr7lKg"
### Bước 1:
Vào cài đặt bật chế độ Active the developer mode(with assets)
### Bước 2:
Vào Technical chọn System Parameters
### Bước 3:
Tạo key "gemini.api_key" và thay đổi giá trị thành "API key của bạn" đã lấy bên trên và save lại
