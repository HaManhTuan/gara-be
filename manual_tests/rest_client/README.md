# REST Client Manual Testing Guide

This directory contains comprehensive REST client files for manual API testing using VS Code REST Client extension.

## 🚀 Quick Setup

### 1. Install VS Code REST Client Extension
- Open VS Code
- Go to Extensions (Ctrl+Shift+X)
- Search for "REST Client"
- Install the extension by Huachao Mao

### 2. Start Your FastAPI Server
```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open REST Client Files
- Open any `.http` file in this directory
- Click "Send Request" above each request
- View responses in VS Code

## 📁 File Structure

| File | Purpose | Description |
|------|---------|-------------|
| `01_auth.http` | Authentication | Login, registration, token management |
| `02_users.http` | User Management | CRUD operations for users |
| `03_system.http` | System Endpoints | Health checks, language settings |
| `04_complete_workflow.http` | End-to-End Testing | Complete workflow from registration to cleanup |
| `05_error_handling.http` | Error Scenarios | Testing various error conditions |
| `06_performance.http` | Performance Testing | Basic performance and load testing |

## 🔧 Configuration

### Environment Variables
Each file uses variables that you can customize:

```http
@baseUrl = http://localhost:8000
@apiVersion = v1
@username = testuser
@email = test@example.com
@password = testpassword123
@accessToken = your_access_token_here
```

### Setting Up Authentication
1. Run the registration request in `01_auth.http` (uses email)
2. Run the login request to get an access token (uses username)
3. Copy the `access_token` from the response
4. Update the `@accessToken` variable in all files
5. Now you can test protected endpoints

## 📋 Testing Workflow

### Basic Testing Flow
1. **Health Check** - Verify server is running
2. **Authentication** - Register and login to get token
3. **Protected Endpoints** - Test user management with token
4. **Error Handling** - Test various error scenarios
5. **Cleanup** - Remove test data

### Complete Workflow Testing
Use `04_complete_workflow.http` for end-to-end testing:
1. Register new user
2. Login to get token
3. Create additional users
4. Update and manage users
5. Test system endpoints
6. Clean up test data

## 🎯 Available Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /register` - User registration (uses email)
- `POST /token` - User login (uses username)
- `GET /profile` - Get current user profile (protected)

### User Management (`/api/v1/users/`)
- `GET /` - List all users (protected)
- `POST /` - Create new user (protected)
- `GET /{id}` - Get user by ID (protected)
- `PUT /{id}` - Update user (protected)
- `PATCH /{id}` - Partial update user (protected)
- `DELETE /{id}` - Delete user (protected)

### System Endpoints
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema
- `GET /api/v1/language/` - Get available languages
- `POST /api/v1/language/set` - Set language preference

## 🔍 Testing Tips

### 1. Token Management
- Copy tokens from login responses
- Update `@accessToken` variable in all files
- Tokens expire, so re-login when needed

### 2. User ID Management
- Copy user IDs from creation responses
- Update `@userId` variable for user-specific tests
- Use actual IDs for update/delete operations

### 3. Error Testing
- Test with invalid tokens
- Test with missing required fields
- Test with invalid data formats
- Test unauthorized access

### 4. Performance Testing
- Run multiple requests in sequence
- Monitor response times
- Check server logs for performance issues

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure FastAPI server is running
   - Check if port 8000 is available
   - Verify base URL in variables

2. **401 Unauthorized**
   - Check if access token is valid
   - Re-login to get fresh token
   - Verify token format (Bearer token)

3. **404 Not Found**
   - Check API version in URL
   - Verify endpoint paths
   - Ensure user ID exists

4. **422 Validation Error**
   - Check request body format
   - Verify required fields are present
   - Check data types and formats

### Debugging Tips
- Check server logs for detailed error information
- Use Swagger UI at `http://localhost:8000/docs` for interactive testing
- Verify request/response formats match API documentation
- Test with curl if REST Client has issues

## 📊 Response Examples

### Successful Login Response
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "user": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    }
}
```

### Error Response Example
```json
{
    "success": false,
    "message": "Validation error",
    "errors": [
        {
            "field": "email",
            "message": "Invalid email format"
        }
    ]
}
```

## 🎉 Next Steps

1. **Automated Testing** - Convert manual tests to automated test suites
2. **Load Testing** - Use tools like Apache Bench or Artillery for load testing
3. **API Documentation** - Update OpenAPI schema with examples
4. **Monitoring** - Set up API monitoring and alerting
5. **CI/CD Integration** - Integrate API tests into deployment pipeline
