# Email OTP Service Documentation

## Tổng quan

Service gửi email và OTP (One-Time Password) cho ứng dụng Gara API. Thay vì gửi OTP qua số điện thoại, hệ thống sẽ gửi OTP qua email.

## Các tính năng

### 1. **Email Service** (`app/services/email_service.py`)
- Gửi OTP qua email
- Xác thực OTP
- Gửi email chào mừng
- Gửi email reset password
- Support HTML templates với Jinja2

### 2. **Email Templates** (`app/templates/email/`)
- `otp.html` - Template cho email OTP
- `welcome.html` - Template cho email chào mừng
- `password_reset.html` - Template cho email reset password

### 3. **Mailpit Container**
- SMTP server để test email locally
- Web UI để xem emails đã gửi
- Không cần cấu hình SMTP thật khi develop

## Cấu hình

### Environment Variables (`.env`)

```env
# Email Configuration
SMTP_HOST=mailpit                    # Use "mailpit" for Docker
SMTP_PORT=1025                       # Mailpit SMTP port
SMTP_USERNAME=                       # Optional for production
SMTP_PASSWORD=                       # Optional for production
SMTP_USE_TLS=False                   # Set True for production
SMTP_USE_SSL=False                   # Set True if using port 465
EMAIL_FROM=noreply@gara-api.com     # Sender email
EMAIL_FROM_NAME=Gara API            # Sender name

# OTP Configuration
OTP_EXPIRY_MINUTES=5                # OTP expiry time
OTP_LENGTH=6                        # Length of OTP code
```

### Production SMTP (Gmail example)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Gara API
```

## Cài đặt Dependencies

```bash
# Install dependencies
poetry install

# Hoặc update dependencies
poetry update
```

## Chạy Docker Containers

```bash
# Start all services including Mailpit
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f mailpit
```

## Truy cập Mailpit Web UI

Sau khi chạy docker-compose, truy cập:

**Mailpit Web UI**: http://localhost:8025

Tất cả emails gửi từ ứng dụng sẽ xuất hiện ở đây.

## API Endpoints

### 1. Gửi OTP qua Email

```http
POST /email/send-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "expiry_minutes": 5  // Optional, mặc định là 5 phút
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "otp": "123456",  // Chỉ hiện khi DEBUG=True
  "expiry_minutes": 5
}
```

### 2. Xác thực OTP

```http
POST /email/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully"
}
```

### 3. Gửi Welcome Email

```http
POST /email/send-welcome
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe"
}
```

### 4. Gửi Password Reset Email

```http
POST /email/send-password-reset
Content-Type: application/json

{
  "email": "user@example.com",
  "reset_token": "abc123def456",
  "reset_url": "https://example.com/reset-password?token=abc123def456"
}
```

## Testing với cURL

```bash
# Gửi OTP
curl -X POST http://localhost:8001/email/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "expiry_minutes": 5
  }'

# Xác thực OTP
curl -X POST http://localhost:8001/email/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'

# Gửi welcome email
curl -X POST http://localhost:8001/email/send-welcome \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "John Doe"
  }'
```

## Sử dụng trong Code

### Import Service

```python
from app.services.email_service import email_service
```

### Gửi OTP

```python
# Gửi OTP
result = await email_service.send_otp_email(
    to_email="user@example.com",
    expiry_minutes=5
)

if result["success"]:
    print(f"OTP sent: {result['otp']}")  # Chỉ trong debug mode
```

### Xác thực OTP

```python
# Xác thực OTP
is_valid = email_service.verify_otp(
    email="user@example.com",
    otp="123456"
)

if is_valid:
    print("OTP is valid!")
else:
    print("OTP is invalid or expired!")
```

### Gửi Welcome Email

```python
success = await email_service.send_welcome_email(
    to_email="user@example.com",
    name="John Doe"
)
```

## OTP Storage

**Development**: OTP được lưu trong memory (dictionary trong EmailService)

**Production**: Nên migrate sang Redis hoặc Database với TTL:

```python
# Redis example (future implementation)
await redis.setex(
    f"otp:{email}",
    expiry_minutes * 60,
    otp
)
```

## Customize Email Templates

Templates nằm ở `app/templates/email/`. Bạn có thể customize HTML/CSS:

```html
<!-- app/templates/email/otp.html -->
<div class="otp-code">{{ otp }}</div>
<div class="expiry">Valid for {{ expiry_minutes }} minutes</div>
```

## Security Best Practices

1. **Không return OTP trong response ở production**
   - Set `DEBUG=False` để ẩn OTP trong response

2. **Rate limiting**
   - Implement rate limiting để tránh spam OTP

3. **OTP expiry**
   - Sử dụng expiry time hợp lý (5-10 phút)

4. **SMTP credentials**
   - Không commit credentials vào git
   - Sử dụng environment variables

5. **Production SMTP**
   - Sử dụng SMTP service như SendGrid, AWS SES, hoặc Gmail với App Password

## Troubleshooting

### Email không gửi được

1. Check Mailpit container:
```bash
docker-compose ps mailpit
docker-compose logs mailpit
```

2. Check SMTP settings trong `.env`

3. Check logs:
```bash
docker-compose logs app | grep email
```

### OTP không hợp lệ

1. Check expiry time
2. Đảm bảo email chính xác
3. OTP chỉ có thể dùng 1 lần

### Mailpit Web UI không truy cập được

1. Check port mapping: `localhost:8025`
2. Check Mailpit container status
3. Check firewall/network settings

## Migration sang Production SMTP

Khi deploy production, thay đổi settings:

```env
# Production SMTP (example: SendGrid)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=True
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name
DEBUG=False  # Ẩn OTP trong response
```

## Next Steps

1. **Integrate với authentication flow**
   - Thêm OTP verification vào register/login
   
2. **Rate limiting**
   - Giới hạn số lần gửi OTP

3. **Redis integration**
   - Migrate OTP storage từ memory sang Redis

4. **Email templates**
   - Thêm nhiều templates khác (notifications, alerts, etc.)

5. **Analytics**
   - Track email delivery rates
   - Monitor OTP usage patterns

## Related Documentation

- [Firebase Authentication](../FIREBASE_SETUP.md)
- [Docker Compose Setup](../docker-compose.yml)
- [API Testing Guide](./api_testing_guide.md)
