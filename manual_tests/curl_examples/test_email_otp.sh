#!/bin/bash

# Email OTP Testing with cURL

BASE_URL="http://localhost:8001"

echo "==================================="
echo "Email OTP Service Testing"
echo "==================================="

# 1. Send OTP
echo -e "\n1. Sending OTP to email..."
SEND_OTP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/email/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "expiry_minutes": 5
  }')

echo "Response:"
echo "$SEND_OTP_RESPONSE" | jq '.'

# Extract OTP from response (only works in DEBUG mode)
OTP=$(echo "$SEND_OTP_RESPONSE" | jq -r '.otp')

echo -e "\nExtracted OTP: $OTP"
echo -e "\n⚠️  Check Mailpit Web UI at: http://localhost:8025"
echo "Press Enter to continue after checking email..."
read -r

# 2. Verify OTP
echo -e "\n2. Verifying OTP..."
if [ "$OTP" != "null" ] && [ -n "$OTP" ]; then
  curl -X POST "$BASE_URL/api/v1/email/verify-otp" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"test@example.com\",
      \"otp\": \"$OTP\"
    }" | jq '.'
else
  echo "OTP not available in response (DEBUG mode disabled or failed to send)"
  echo "Please manually enter OTP from email:"
  read -r MANUAL_OTP
  curl -X POST "$BASE_URL/api/v1/email/verify-otp" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"test@example.com\",
      \"otp\": \"$MANUAL_OTP\"
    }" | jq '.'
fi

# 3. Send Welcome Email
echo -e "\n3. Sending welcome email..."
curl -X POST "$BASE_URL/api/v1/email/send-welcome" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "John Doe"
  }' | jq '.'

# 4. Send Password Reset Email
echo -e "\n4. Sending password reset email..."
curl -X POST "$BASE_URL/api/v1/email/send-password-reset" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "reset_token": "abc123def456",
    "reset_url": "http://localhost:8001/reset-password?token=abc123def456"
  }' | jq '.'

echo -e "\n==================================="
echo "Testing Complete!"
echo "Check all emails at: http://localhost:8025"
echo "==================================="
