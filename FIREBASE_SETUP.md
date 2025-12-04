# Hướng dẫn Setup Firebase Authentication

## Tổng quan

API đã được cấu hình để hỗ trợ Firebase Authentication cho mobile apps. File Firebase service account đã có sẵn tại `app/config/fixautocar-26c43-firebase-adminsdk-fbsvc-923b1076a1.json`.

## Cấu hình đã hoàn tất

✅ Firebase Admin SDK đã được cài đặt  
✅ User model hỗ trợ phone authentication (email nullable, phone unique)  
✅ API endpoint `/api/auth/verify-token` đã sẵn sàng  
✅ Migration database đã chạy thành công

## Cấu trúc Database

Bảng `users` hiện tại:
- `id`: bigint (auto-increment)
- `username`: string (unique, required)
- `email`: string (unique, **nullable** - cho phone auth)
- `phone_number`: string (unique, nullable)
- `phone_verified`: boolean
- `full_name`: string (nullable)
- `hashed_password`: string (required)
- `is_superuser`: boolean
- `created_at`, `updated_at`, `deleted_at`: timestamps

## API Endpoint

### POST /api/auth/verify-token

**Request:**
```json
{
  "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI..."
}
```

**Response (Phone Login - User mới):**
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": 1,
    "username": "user_0912345678",
    "email": null,
    "phone_number": "+84912345678",
    "full_name": "+84912345678",
    "is_new_user": true
  }
}
```

**Response (Email Login - User đã tồn tại):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": 2,
    "username": "john.doe",
    "email": "john.doe@example.com",
    "phone_number": null,
    "full_name": "John Doe",
    "is_new_user": false
  }
}
```

## Logic Authentication

1. **Mobile app** đăng nhập qua Firebase (Phone OTP / Email / Google / etc.)
2. **Mobile app** lấy Firebase ID token
3. **Mobile app** gửi token lên endpoint `/api/auth/verify-token`
4. **Backend** verify token với Firebase Admin SDK
5. **Backend** kiểm tra user trong database:
   - Tìm theo `email` (nếu có)
   - Tìm theo `phone_number` (nếu có)
   - Nếu không tìm thấy → Tạo user mới (**Register**)
   - Nếu tìm thấy → Trả về user hiện tại (**Login**)
6. **Backend** tạo JWT token và trả về cho mobile app
7. **Mobile app** lưu JWT token để authenticate các API calls khác

## Testing

### 1. Kiểm tra API docs
```bash
http://localhost:8001/docs
```

### 2. Test với Firebase token từ mobile
```bash
curl -X POST http://localhost:8001/api/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "YOUR_FIREBASE_ID_TOKEN_FROM_MOBILE"
  }'
```

### 3. Sử dụng JWT token nhận được
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8001/api/auth/profile
```

## Mobile App Integration

### Flutter Example
```dart
import 'package:firebase_auth/firebase_auth.dart';

// Login with phone
Future<void> loginWithPhone(String phoneNumber) async {
  await FirebaseAuth.instance.verifyPhoneNumber(
    phoneNumber: phoneNumber,
    verificationCompleted: (PhoneAuthCredential credential) async {
      await FirebaseAuth.instance.signInWithCredential(credential);
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();
      
      // Call backend API
      final response = await http.post(
        Uri.parse('http://your-api/api/auth/verify-token'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'firebase_token': idToken}),
      );
      
      final data = json.decode(response.body);
      // Save data['access_token'] for future API calls
    },
    // ... other callbacks
  );
}
```

### React Native Example
```javascript
import auth from '@react-native-firebase/auth';

async function loginWithPhone(phoneNumber) {
  const confirmation = await auth().signInWithPhoneNumber(phoneNumber);
  const credential = await confirmation.confirm(code);
  
  const idToken = await auth().currentUser.getIdToken();
  
  const response = await fetch('http://your-api/api/auth/verify-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ firebase_token: idToken })
  });
  
  const { access_token, is_new_user } = await response.json();
  // Save access_token for future API calls
}
```

## Lưu ý quan trọng

1. **Email có thể null**: User đăng nhập bằng phone sẽ không có email
2. **Phone có thể null**: User đăng nhập bằng email sẽ không có phone
3. **Username tự động tạo**:
   - Từ email: `john.doe@example.com` → username: `john.doe` (hoặc `john.doe1` nếu trùng)
   - Từ phone: `+84912345678` → username: `user_84912345678`
   - Fallback: `user_` + Firebase UID
4. **Firebase token expire**: Token thường expire sau 1 giờ, mobile app cần refresh
5. **JWT token expire**: Mặc định 30 phút (cấu hình trong `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)

## Troubleshooting

### Warning: Firebase service account file not found
- File đang tồn tại nhưng chưa được mount vào container
- App vẫn chạy được nhưng API verify-token sẽ trả lỗi 500
- Cần mount file vào container hoặc dùng environment variable

### Error: Invalid Firebase token
- Token đã hết hạn
- Token không hợp lệ
- Sai project Firebase

### Error: Email/Phone already exists
- User đã tồn tại trong hệ thống
- Đây là login, không phải register

## Cấu hình Production

Khi deploy production, **không nên** commit file Firebase service account vào git. Thay vào đó:

1. Dùng environment variable:
```bash
FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

2. Hoặc mount file từ secret management service
