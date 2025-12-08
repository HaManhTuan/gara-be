# Email OTP Service - Quick Start Guide

## 🚀 Khởi động nhanh

### 1. Cài đặt dependencies

```bash
poetry install
```

### 2. Khởi động Docker containers

```bash
docker-compose up -d
```

Services sẽ chạy:
- **App**: http://localhost:8001
- **Mailpit Web UI**: http://localhost:8025 (để xem emails)
- **Database**: localhost:5433
- **Redis**: localhost:6380

### 3. Kiểm tra services

```bash
docker-compose ps
```

## 📧 Test gửi OTP qua Email

### Cách 1: Sử dụng Swagger UI

1. Truy cập: http://localhost:8001/docs
2. Tìm endpoint **POST /api/v1/email/send-otp**
3. Click "Try it out"
4. Nhập:
```json
{
  "email": "test@example.com",
  "expiry_minutes": 5
}
```
5. Click "Execute"
6. Xem email tại: http://localhost:8025

### Cách 2: Sử dụng cURL

```bash
# Gửi OTP
curl -X POST http://localhost:8001/api/v1/email/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "expiry_minutes": 5
  }'

# Xác thực OTP (thay 123456 bằng OTP từ email)
curl -X POST http://localhost:8001/api/v1/email/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'
```

### Cách 3: Chạy script test tự động

```bash
chmod +x manual_tests/curl_examples/test_email_otp.sh
./manual_tests/curl_examples/test_email_otp.sh
```

## 📝 Các API Endpoints

### Email OTP Login Flow (Chính)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/auth/email/login` | **Bước 1:** Gửi OTP qua email để login |
| POST | `/api/v1/auth/email/verify` | **Bước 2:** Xác thực OTP và nhận JWT token |

### Email Utilities

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/email/send-otp` | Gửi OTP qua email (generic) |
| POST | `/api/v1/email/verify-otp` | Xác thực OTP (generic) |
| POST | `/api/v1/email/send-welcome` | Gửi email chào mừng |
| POST | `/api/v1/email/send-password-reset` | Gửi email reset password |

## 🔍 Xem Emails

Tất cả emails gửi từ app sẽ được Mailpit bắt và hiển thị tại:

**http://localhost:8025**

Không có email thật nào được gửi khi develop.

## ⚙️ Cấu hình

File `.env`:

```env
# Email (Development - Mailpit)
SMTP_HOST=mailpit
SMTP_PORT=1025
EMAIL_FROM=noreply@gara-api.com
EMAIL_FROM_NAME=Gara API

# OTP
OTP_EXPIRY_MINUTES=5
OTP_LENGTH=6
DEBUG=True  # Hiển thị OTP trong response
```

## 🐛 Troubleshooting

### Email không gửi được?

```bash
# Check Mailpit logs
docker-compose logs mailpit

# Restart Mailpit
docker-compose restart mailpit
```

### Không thấy email trong Mailpit?

1. Check app logs: `docker-compose logs app | grep email`
2. Verify SMTP settings trong `.env`
3. Restart app: `docker-compose restart app`

### OTP không hợp lệ?

- OTP chỉ valid trong 5 phút (default)
- Mỗi OTP chỉ dùng được 1 lần
- Đảm bảo email chính xác

## 📚 Documentation đầy đủ

Xem chi tiết tại: [docs/email_otp_service.md](../../docs/email_otp_service.md)

## 🔐 Production Setup

Khi deploy production, update `.env`:

```env
# Production SMTP (Example: Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True
EMAIL_FROM=your-email@gmail.com
DEBUG=False  # Ẩn OTP trong response
```

## 📞 Support

Nếu gặp vấn đề, check:
1. Docker logs: `docker-compose logs`
2. Mailpit UI: http://localhost:8025
3. API docs: http://localhost:8001/docs
4. Full docs: `docs/email_otp_service.md`
