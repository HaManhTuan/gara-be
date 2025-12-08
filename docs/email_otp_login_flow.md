# Email OTP Login Flow - Complete Guide

## 📋 Overview

Flow đăng nhập sử dụng OTP qua email thay vì password. User chỉ cần email để login, không cần remember password.

## 🔄 Login Flow

```
User nhập email
    ↓
POST /auth/email/login (Step 1)
    ↓
System gửi OTP qua email
    ↓
User nhận OTP từ email
    ↓
POST /auth/email/verify (Step 2)
    ↓
System xác thực OTP
    ↓
Return JWT access_token
    ↓
User logged in ✅
```

## 🏗️ Architecture

### Storage: Redis
- ✅ **OTP storage**: `otp:{email}` key với TTL
- ✅ **Auto-expire**: TTL = 5 phút (configurable)
- ✅ **One-time use**: OTP tự động xóa sau khi verify
- ✅ **Scalable**: Phù hợp cho production

### Database: PostgreSQL
- ✅ **User model**: Lưu email, username, profile
- ✅ **Auto-create**: Tự động tạo user nếu chưa tồn tại
- ✅ **Email unique**: Mỗi email chỉ một account

## 📝 API Documentation

### Step 1: Initiate Login (Send OTP)

**Endpoint:** `POST /api/v1/auth/email/login`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "success": true,
    "message": "OTP sent to your email",
    "email": "user@example.com",
    "expiry_minutes": 5,
    "otp": "123456"  // Chỉ hiện khi DEBUG=True
  }
}
```

**Logic:**
1. Check email tồn tại → nếu không thì tạo user mới
2. Generate OTP (6 digits)
3. Store OTP trong Redis với TTL
4. Send email với OTP
5. Return success

**Use Cases:**
- ✅ User mới: Tự động tạo account
- ✅ User cũ: Gửi OTP để login
- ✅ Email không hợp lệ: Return 422 validation error

---

### Step 2: Verify OTP & Get Token

**Endpoint:** `POST /api/v1/auth/email/verify`

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "success": true,
    "message": "Login successful",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Response (Failed):**
```json
{
  "success": false,
  "message": "Invalid or expired OTP",
  "data": null
}
```

**Logic:**
1. Verify OTP từ Redis
2. Check user exists & is_active
3. Generate JWT access token
4. Delete OTP từ Redis
5. Return token

**Error Cases:**
- ❌ OTP invalid: Return 401 Unauthorized
- ❌ OTP expired: Return 401 Unauthorized
- ❌ User inactive: Return 401 Unauthorized
- ❌ User not found: Return 404 Not Found

---

## 🧪 Testing

### Using cURL

```bash
# Step 1: Send OTP
curl -X POST http://localhost:8001/api/v1/auth/email/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Response will include OTP in DEBUG mode
# {"success":true,"data":{"otp":"123456",...}}

# Step 2: Verify OTP and get token
curl -X POST http://localhost:8001/api/v1/auth/email/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'

# Response will include access_token
# Use this token for authenticated requests
```

### Using Access Token

```bash
# Use token in Authorization header
curl -X GET http://localhost:8001/api/v1/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Testing Script

```bash
#!/bin/bash

EMAIL="test@example.com"

echo "Step 1: Sending OTP..."
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/email/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}")

echo "$RESPONSE" | jq '.'

# Extract OTP (only works in DEBUG mode)
OTP=$(echo "$RESPONSE" | jq -r '.data.otp')

echo -e "\nStep 2: Verifying OTP: $OTP"
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/email/verify \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"$OTP\"}")

echo "$TOKEN_RESPONSE" | jq '.'

# Extract access token
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.data.access_token')

echo -e "\nStep 3: Testing authenticated request..."
curl -X GET http://localhost:8001/api/v1/auth/profile \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
```

## 🔧 Configuration

### Environment Variables

```env
# Redis (OTP Storage)
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0

# Email (Mailpit for dev)
SMTP_HOST=mailpit
SMTP_PORT=1025
EMAIL_FROM=noreply@gara-api.com

# OTP Settings
OTP_EXPIRY_MINUTES=5
OTP_LENGTH=6

# Debug (show OTP in response)
DEBUG=True

# JWT Token
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🔒 Security Considerations

### 1. OTP Storage in Redis
- ✅ **TTL**: Auto-expire sau 5 phút
- ✅ **One-time use**: Xóa sau khi verify
- ✅ **Isolated**: Key format `otp:{email}`

### 2. Rate Limiting (TODO)
```python
# Implement rate limiting để tránh abuse
# Max 3 OTP requests per email per 5 minutes
```

### 3. Production Settings
```env
DEBUG=False  # Ẩn OTP trong response
SMTP_HOST=smtp.gmail.com  # Real SMTP server
SMTP_PORT=587
SMTP_USE_TLS=True
```

### 4. OTP Best Practices
- ✅ 6 digit code (balance security vs usability)
- ✅ 5 minute expiry (enough time but not too long)
- ✅ One-time use (prevent replay attacks)
- ⚠️ Consider: SMS backup, email verification

## 🚀 Production Deployment

### 1. Redis Setup
```yaml
# docker-compose.yml
redis:
  image: redis:alpine
  command: redis-server --requirepass your-redis-password
  volumes:
    - redis_data:/data
```

### 2. Email Provider
```env
# Use production SMTP (SendGrid, AWS SES, etc.)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=True
```

### 3. Monitoring
- Monitor OTP send rate
- Track failed verification attempts
- Alert on high failure rate

## 📊 Database Schema

### User Model
```python
class User(BaseModel):
    username: str  # Auto-generated from email
    email: str  # Unique, indexed
    full_name: str
    hashed_password: str  # Not used for OTP login
    is_active: bool
    phone_number: str  # Optional
    phone_verified: bool
    is_superuser: bool
```

### Auto-generated Username
```python
# From email: "john.doe@example.com"
# Username: "john.doe"

# If exists: "john.doe1", "john.doe2", etc.
```

## 🔄 Integration Examples

### Frontend (React/Vue/Angular)

```javascript
// Step 1: Send OTP
async function sendOTP(email) {
  const response = await fetch('/api/v1/auth/email/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  
  const data = await response.json();
  return data;
}

// Step 2: Verify OTP
async function verifyOTP(email, otp) {
  const response = await fetch('/api/v1/auth/email/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Store token
    localStorage.setItem('access_token', data.data.access_token);
    return true;
  }
  return false;
}

// Use authenticated requests
async function getProfile() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/v1/auth/profile', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Mobile (React Native)

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Login flow
async function login(email) {
  // Step 1: Send OTP
  const sendResult = await sendOTP(email);
  
  if (!sendResult.success) {
    Alert.alert('Error', 'Failed to send OTP');
    return;
  }
  
  // Show OTP input screen
  navigation.navigate('OTPScreen', { email });
}

async function verifyAndLogin(email, otp) {
  // Step 2: Verify OTP
  const verifyResult = await verifyOTP(email, otp);
  
  if (verifyResult.success) {
    // Save token
    await AsyncStorage.setItem('token', verifyResult.data.access_token);
    
    // Navigate to home
    navigation.reset({
      index: 0,
      routes: [{ name: 'Home' }],
    });
  } else {
    Alert.alert('Error', 'Invalid OTP');
  }
}
```

## 🐛 Troubleshooting

### OTP không gửi được
1. Check Redis connection: `docker-compose logs redis`
2. Check email service: `docker-compose logs mailpit`
3. Check app logs: `docker-compose logs app | grep OTP`

### OTP không hợp lệ
1. Check expiry time (default 5 minutes)
2. Check Redis key exists: `redis-cli GET otp:user@example.com`
3. Verify email chính xác

### User không tạo được
1. Check email unique constraint
2. Check database connection
3. View logs for specific error

## 📚 Related Documentation

- [Email Service Documentation](./email_otp_service.md)
- [Redis Client Documentation](../app/utils/redis_client.py)
- [User Service Documentation](./services_guide.md)
- [Authentication Guide](./firebase_authentication.md)

## ⏭️ Next Steps

1. **Implement rate limiting** để tránh spam
2. **Add email verification** cho new users
3. **Support multiple OTP delivery methods** (SMS, WhatsApp)
4. **Add "Remember me"** functionality
5. **Implement refresh tokens** for longer sessions
