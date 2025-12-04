# REST Client Setup for Manual API Testing

This directory contains REST client configurations and example requests for testing the FastAPI application manually.

## Setup Options

### Option 1: VS Code REST Client Extension (Recommended)
1. Install the "REST Client" extension in VS Code
2. Use the `.http` files in this directory to make API requests
3. Click "Send Request" above each request to execute it

### Option 2: Postman
1. Import the `postman_collection.json` file into Postman
2. Set up environment variables for base URL and tokens
3. Run requests from the collection

### Option 3: Insomnia
1. Import the `insomnia_collection.json` file into Insomnia
2. Configure environment variables
3. Execute requests from the collection

### Option 4: curl Commands
Use the shell scripts in the `curl_examples/` directory for command-line testing.

## Environment Variables

Set these variables in your REST client:

```
BASE_URL=http://localhost:8000
API_VERSION=v1
USERNAME=test@example.com
PASSWORD=testpassword123
```

## Authentication Flow

1. **Register** a new user (if needed)
2. **Login** to get access token
3. **Use token** in Authorization header for protected endpoints

## Available Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user profile (protected)

### User Management
- `GET /api/v1/users/` - List users (protected)
- `POST /api/v1/users/` - Create user (protected)
- `GET /api/v1/users/{id}` - Get user by ID (protected)
- `PUT /api/v1/users/{id}` - Update user (protected)
- `DELETE /api/v1/users/{id}` - Delete user (protected)

### System
- `GET /health` - Health check
- `GET /api/v1/language/` - Get available languages
- `POST /api/v1/language/set` - Set language preference

## Quick Start

1. Start your FastAPI server: `poetry run uvicorn main:app --reload`
2. Open VS Code with REST Client extension
3. Open any `.http` file in this directory
4. Click "Send Request" to test endpoints
5. Check the response and status codes

## Tips

- Use the `auth.http` file to get authentication tokens
- Copy tokens from login responses to use in other requests
- Check the server logs for detailed error information
- Use Swagger UI at `http://localhost:8000/docs` for interactive testing
