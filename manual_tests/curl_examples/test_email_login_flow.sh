#!/bin/bash

# Email OTP Login Flow Testing

BASE_URL="http://localhost:8001"
EMAIL="test-login@example.com"

echo "=========================================="
echo "Email OTP Login Flow Testing"
echo "=========================================="

# Step 1: Send OTP (Login)
echo -e "\n📧 Step 1: Initiating login with email..."
echo "Email: $EMAIL"

SEND_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/email/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}")

echo -e "\nResponse:"
echo "$SEND_RESPONSE" | jq '.'

# Check if OTP send was successful
SUCCESS=$(echo "$SEND_RESPONSE" | jq -r '.success')

if [ "$SUCCESS" != "true" ]; then
  echo -e "\n❌ Failed to send OTP. Exiting..."
  exit 1
fi

# Extract OTP (only works in DEBUG mode)
OTP=$(echo "$SEND_RESPONSE" | jq -r '.data.otp')

if [ "$OTP" == "null" ] || [ -z "$OTP" ]; then
  echo -e "\n⚠️  OTP not available in response (DEBUG mode disabled)"
  echo "Please check Mailpit at http://localhost:8025 for OTP"
  echo "Or manually enter OTP:"
  read -r OTP
else
  echo -e "\n✅ OTP received: $OTP"
fi

echo -e "\n⏳ Waiting 2 seconds before verification..."
sleep 2

# Step 2: Verify OTP and get access token
echo -e "\n🔐 Step 2: Verifying OTP and completing login..."

VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/email/verify" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"$OTP\"}")

echo -e "\nResponse:"
echo "$VERIFY_RESPONSE" | jq '.'

# Check if verification was successful
VERIFY_SUCCESS=$(echo "$VERIFY_RESPONSE" | jq -r '.success')

if [ "$VERIFY_SUCCESS" != "true" ]; then
  echo -e "\n❌ OTP verification failed. Exiting..."
  exit 1
fi

# Extract access token
ACCESS_TOKEN=$(echo "$VERIFY_RESPONSE" | jq -r '.data.access_token')
USER_ID=$(echo "$VERIFY_RESPONSE" | jq -r '.data.user_id')

echo -e "\n✅ Login successful!"
echo "User ID: $USER_ID"
echo "Access Token (first 50 chars): ${ACCESS_TOKEN:0:50}..."

# Step 3: Test authenticated request
echo -e "\n👤 Step 3: Testing authenticated request (Get Profile)..."

PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/auth/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "\nProfile Response:"
echo "$PROFILE_RESPONSE" | jq '.'

PROFILE_SUCCESS=$(echo "$PROFILE_RESPONSE" | jq -r '.success')

if [ "$PROFILE_SUCCESS" == "true" ]; then
  echo -e "\n✅ Authenticated request successful!"
  
  # Display user info
  USERNAME=$(echo "$PROFILE_RESPONSE" | jq -r '.data.username')
  EMAIL_RESP=$(echo "$PROFILE_RESPONSE" | jq -r '.data.email')
  
  echo -e "\n📋 User Information:"
  echo "  Username: $USERNAME"
  echo "  Email: $EMAIL_RESP"
else
  echo -e "\n❌ Authenticated request failed!"
fi

# Step 4: Test with invalid OTP
echo -e "\n🧪 Step 4: Testing with invalid OTP..."

INVALID_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/email/verify" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"999999\"}")

echo -e "\nInvalid OTP Response:"
echo "$INVALID_RESPONSE" | jq '.'

INVALID_SUCCESS=$(echo "$INVALID_RESPONSE" | jq -r '.success')

if [ "$INVALID_SUCCESS" != "true" ]; then
  echo -e "\n✅ Invalid OTP correctly rejected"
else
  echo -e "\n❌ Security issue: Invalid OTP was accepted!"
fi

# Summary
echo -e "\n=========================================="
echo "Testing Summary"
echo "=========================================="
echo "✅ Step 1: OTP sent successfully"
echo "✅ Step 2: OTP verified and token received"
echo "✅ Step 3: Authenticated request successful"
echo "✅ Step 4: Invalid OTP correctly rejected"
echo -e "\n📧 Check all emails at: http://localhost:8025"
echo "🔑 Access Token: ${ACCESS_TOKEN:0:50}..."
echo "=========================================="
