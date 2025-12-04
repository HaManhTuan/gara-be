#!/bin/bash

# Manual API Testing - curl Examples
# Comprehensive curl-based testing for FastAPI application

# Configuration
BASE_URL="http://localhost:8000"
API_VERSION="v1"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="testpassword123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Manual API Testing - curl Examples${NC}"
echo -e "${BLUE}Base URL: ${BASE_URL}${NC}"
echo -e "${BLUE}API Version: ${API_VERSION}${NC}"
echo ""

# Function to make API calls with better formatting
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local headers=$4
    local description=$5

    echo -e "${YELLOW}📡 ${method} ${endpoint}${NC}"
    if [ -n "$description" ]; then
        echo -e "${BLUE}   ${description}${NC}"
    fi

    if [ -n "$data" ]; then
        curl -X ${method} \
             -H "Content-Type: application/json" \
             ${headers} \
             -d "${data}" \
             "${BASE_URL}${endpoint}" \
             -w "\n${GREEN}Status: %{http_code}${NC}\n" \
             -s | jq . 2>/dev/null || cat
    else
        curl -X ${method} \
             ${headers} \
             "${BASE_URL}${endpoint}" \
             -w "\n${GREEN}Status: %{http_code}${NC}\n" \
             -s | jq . 2>/dev/null || cat
    fi
    echo ""
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq not found. Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)${NC}"
    echo -e "${YELLOW}   JSON responses will not be formatted${NC}"
    echo ""
fi

# 1. Health Check
echo -e "${GREEN}1. Health Check${NC}"
make_request "GET" "/health" "" "" "Check if server is running"

# 2. API Documentation
echo -e "${GREEN}2. API Documentation${NC}"
echo -e "${BLUE}   Swagger UI: ${BASE_URL}/docs${NC}"
echo -e "${BLUE}   ReDoc: ${BASE_URL}/redoc${NC}"
echo ""

# 3. User Registration
echo -e "${GREEN}3. User Registration${NC}"
REGISTER_DATA='{
    "username": "testuser",
    "email": "'${TEST_EMAIL}'",
    "password": "'${TEST_PASSWORD}'",
    "full_name": "Test User"
}'
make_request "POST" "/api/${API_VERSION}/auth/register" "${REGISTER_DATA}" "" "Register new user"

# 4. User Login
echo -e "${GREEN}4. User Login${NC}"
LOGIN_DATA='{
    "username": "'${TEST_EMAIL}'",
    "password": "'${TEST_PASSWORD}'"
}'
LOGIN_RESPONSE=$(make_request "POST" "/api/${API_VERSION}/auth/login" "${LOGIN_DATA}" "" "Login to get access token")

# Extract access token (basic extraction - you may need to manually copy)
echo -e "${YELLOW}📋 Manual Step Required:${NC}"
echo -e "${BLUE}   1. Copy the 'access_token' from the login response above${NC}"
echo -e "${BLUE}   2. Set ACCESS_TOKEN variable: export ACCESS_TOKEN='your_token_here'${NC}"
echo -e "${BLUE}   3. Run this script again to test protected endpoints${NC}"
echo ""

# Check if ACCESS_TOKEN is set
if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "your_token_here" ]; then
    echo -e "${GREEN}5. Get Current User Profile${NC}"
    make_request "GET" "/api/${API_VERSION}/auth/me" "" "-H 'Authorization: Bearer ${ACCESS_TOKEN}'" "Get current user info"

    echo -e "${GREEN}6. List All Users${NC}"
    make_request "GET" "/api/${API_VERSION}/users/" "" "-H 'Authorization: Bearer ${ACCESS_TOKEN}'" "List all users"

    echo -e "${GREEN}7. Create New User${NC}"
    CREATE_USER_DATA='{
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "is_active": true
    }'
    CREATE_RESPONSE=$(make_request "POST" "/api/${API_VERSION}/users/" "${CREATE_USER_DATA}" "-H 'Authorization: Bearer ${ACCESS_TOKEN}'" "Create new user")

    echo -e "${GREEN}8. Test Language Settings${NC}"
    LANGUAGE_DATA='{
        "language": "en"
    }'
    make_request "POST" "/api/${API_VERSION}/language/set" "${LANGUAGE_DATA}" "" "Set language preference"

    echo -e "${GREEN}9. Get Available Languages${NC}"
    make_request "GET" "/api/${API_VERSION}/language/" "" "" "Get available languages"

    echo -e "${GREEN}10. Test Error Handling${NC}"
    make_request "GET" "/api/${API_VERSION}/nonexistent" "" "" "Test 404 error"

else
    echo -e "${RED}⚠️  ACCESS_TOKEN not set. Please follow the manual steps above.${NC}"
fi

echo -e "${GREEN}✅ curl testing completed!${NC}"
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "${BLUE}   - Use 'export ACCESS_TOKEN=your_token' to set token${NC}"
echo -e "${BLUE}   - Install jq for better JSON formatting${NC}"
echo -e "${BLUE}   - Check server logs for detailed error information${NC}"
