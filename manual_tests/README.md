# Manual API Testing Suite

This directory contains comprehensive manual testing tools and examples for the FastAPI application using VS Code REST Client.

## 📁 Directory Structure

```
manual_tests/
├── rest_client/          # VS Code REST Client files (.http)
│   ├── 01_auth.http      # Authentication endpoints
│   ├── 02_users.http     # User management endpoints
│   ├── 03_system.http    # System and utility endpoints
│   ├── 04_complete_workflow.http # End-to-end testing
│   ├── 05_error_handling.http    # Error scenarios
│   ├── 06_performance.http       # Performance testing
│   └── README.md         # Detailed REST client guide
└── README.md             # This file
```

## 🚀 Quick Start

### VS Code REST Client (Recommended)
1. Install "REST Client" extension in VS Code
2. Start FastAPI server: `poetry run uvicorn main:app --reload`
3. Open any `.http` file in `rest_client/` directory
4. Click "Send Request" above each request
5. View responses directly in VS Code

## 🔧 Environment Setup

### Required Environment Variables
```bash
BASE_URL=http://localhost:8000
API_VERSION=v1
TEST_EMAIL=test@example.com
TEST_PASSWORD=testpassword123
```

### Server Setup
```bash
# Start the FastAPI server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with specific settings
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 📋 Testing Workflow

1. **Start Server**: Ensure FastAPI server is running
2. **Health Check**: Verify server is accessible
3. **Authentication**: Register/login to get access token
4. **API Testing**: Test various endpoints with token
5. **Cleanup**: Remove test data if needed

## 🎯 Available Test Categories

- **Authentication**: Login, registration, token management
- **User Management**: CRUD operations for users
- **System**: Health checks, language settings
- **Error Handling**: Invalid requests, unauthorized access
- **Complete Workflow**: End-to-end testing scenarios

## 📖 Documentation

- `documentation/` - Detailed testing guides
- `README.md` - This file
- Individual tool documentation in respective folders

## 🔍 Tips for Manual Testing

1. **Use Swagger UI**: Visit `http://localhost:8000/docs` for interactive testing
2. **Check Logs**: Monitor server logs for detailed error information
3. **Token Management**: Copy tokens from login responses for protected endpoints
4. **Environment Variables**: Set up variables for easy configuration changes
5. **Response Validation**: Verify status codes and response formats

## 🎯 Testing Categories

| File | Category | Description |
|------|----------|-------------|
| `01_auth.http` | Authentication | Login, registration, token management |
| `02_users.http` | User Management | CRUD operations for users |
| `03_system.http` | System Endpoints | Health checks, language settings |
| `04_complete_workflow.http` | End-to-End Testing | Complete workflow from registration to cleanup |
| `05_error_handling.http` | Error Scenarios | Testing various error conditions |
| `06_performance.http` | Performance Testing | Basic performance and load testing |

## 📝 Contributing

When adding new test cases:
1. Follow the existing naming conventions
2. Include proper error handling examples
3. Document any special requirements
4. Update this README if adding new categories
