# Firebase Authentication Setup Guide

## Overview

API này hỗ trợ xác thực Firebase cho mobile apps. Mobile apps có thể đăng nhập qua Firebase (Google, Email/Password, etc.) và gửi Firebase ID token lên backend để nhận JWT token.

## Cấu hình Firebase Admin SDK

### Bước 1: Lấy Service Account Key từ Firebase Console

1. Truy cập [Firebase Console](https://console.firebase.google.com/)
2. Chọn project của bạn
3. Vào **Project Settings** (Settings icon) → **Service Accounts**
4. Click **Generate new private key**
5. Download file JSON (ví dụ: `firebase-service-account.json`)

### Bước 2: Cấu hình trong Backend

Có 2 cách để cấu hình:

#### Cách 1: Sử dụng file JSON (Recommended for Development)

1. Đặt file service account JSON vào thư mục project (ví dụ: `/app/config/firebase-service-account.json`)
2. Thêm vào `.env`:
```env
FIREBASE_SERVICE_ACCOUNT_PATH=/app/config/firebase-service-account.json
```

3. Trong `docker-compose.yml`, mount file vào container:
```yaml
volumes:
  - ./:/app
  - ./config/firebase-service-account.json:/app/config/firebase-service-account.json:ro
```

#### Cách 2: Sử dụng Environment Variable (Recommended for Production)

1. Convert file JSON thành string (1 dòng):
```bash
cat firebase-service-account.json | jq -c
```

2. Thêm vào `.env` hoặc environment variables:
```env
FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project",...}'
```

### Bước 3: Cập nhật docker-compose.yml

Thêm environment variable vào service `app`:

```yaml
environment:
  - FIREBASE_SERVICE_ACCOUNT_PATH=/app/config/firebase-service-account.json
  # OR
  - FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

## API Usage

### Endpoint: POST /api/auth/verify-token

Mobile app gửi Firebase ID token để verify và nhận JWT token.

#### Request

```json
{
  "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOW..."
}
```

#### Response (Login - User đã tồn tại)

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": 123,
    "username": "user@example.com",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_new_user": false
  }
}
```

#### Response (Register - User mới)

```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": 124,
    "username": "newuser",
    "email": "newuser@example.com",
    "full_name": "Jane Smith",
    "is_new_user": true
  }
}
```

### Mobile App Flow

1. User đăng nhập qua Firebase (Google, Email, etc.)
2. Lấy Firebase ID token:
   ```javascript
   const idToken = await firebase.auth().currentUser.getIdToken();
   ```
3. Gửi token lên backend:
   ```javascript
   const response = await fetch('http://api.example.com/api/auth/verify-token', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ firebase_token: idToken })
   });
   ```
4. Nhận JWT token và lưu để authenticate các API calls tiếp theo:
   ```javascript
   const { access_token, is_new_user } = await response.json();
   // Save access_token for future API calls
   ```

### Sử dụng JWT Token

Sau khi nhận JWT token, sử dụng nó cho các API calls khác:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8001/api/auth/profile
```

## Testing

### Test với cURL (sau khi có Firebase token từ mobile)

```bash
curl -X POST http://localhost:8001/api/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "YOUR_FIREBASE_ID_TOKEN"
  }'
```

## Security Notes

1. **Không commit** file service account JSON vào git
2. Thêm vào `.gitignore`:
   ```
   config/firebase-service-account.json
   **/firebase-service-account*.json
   ```
3. Trong production, sử dụng environment variable hoặc secret management service
4. Firebase ID token có thời gian expire ngắn (thường 1 giờ), mobile app cần refresh token khi hết hạn
5. JWT token do backend tạo có thời gian expire theo cấu hình `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

## Logic xử lý

1. **Verify Firebase token**: Backend verify Firebase ID token với Firebase Admin SDK
2. **Get user info**: Lấy thông tin user từ Firebase (email, name, uid, etc.)
3. **Check existing user**: Tìm user trong database theo email
   - Nếu tồn tại → Login (is_new_user = false)
   - Nếu không tồn tại → Register (is_new_user = true)
4. **Create JWT**: Tạo JWT token cho user
5. **Return response**: Trả về JWT token và thông tin user

## Troubleshooting

### Error: Firebase service not configured

- Kiểm tra `FIREBASE_SERVICE_ACCOUNT_PATH` hoặc `FIREBASE_SERVICE_ACCOUNT_JSON` đã được set
- Kiểm tra file JSON có đúng format và đường dẫn

### Error: Invalid Firebase token

- Token đã hết hạn, mobile app cần refresh token
- Token không hợp lệ hoặc không đúng project

### Error: Email already exists (từ traditional registration)

- User đã đăng ký bằng username/password truyền thống
- Cần merge accounts hoặc sử dụng email khác
