# API Testing Guide

This document provides guidance on how to write effective API tests for the FastAPI MVC application.

## Testing Approach

Our API testing approach follows these principles:

1. **Isolated Tests**: Each test should be independent and should not depend on the state from previous tests.
2. **Test Database**: Tests use a separate database (SQLite in-memory by default) to avoid affecting the production database.
3. **Fixture-Based Setup**: We use pytest fixtures to set up test data and dependencies.
4. **Authentication Handling**: Helper functions are provided to simulate authentication for protected endpoints.

## Test Structure

### Basic Structure

API tests typically follow this structure:

```python
@pytest.mark.asyncio
async def test_some_endpoint(client: TestClient, db: AsyncSession):
    # 1. Setup (create test data, prepare request)

    # 2. Execute the API call
    response = client.get("/some-endpoint")

    # 3. Assert the response
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    # Additional assertions...
```

### Testing Authenticated Endpoints

For endpoints that require authentication:

```python
@pytest.mark.asyncio
async def test_protected_endpoint(client: TestClient, db: AsyncSession):
    # 1. Create a test user
    user = await create_test_user(db)

    # 2. Generate a token
    token = create_test_token(user.id)

    # 3. Make a request with authentication
    response = client.get(
        "/protected-endpoint",
        headers=get_auth_headers(token)
    )

    # 4. Assert the response
    assert response.status_code == 200
    # Additional assertions...
```

## Test Categories

### 1. Health Checks

Test basic health check endpoints to verify the service and database are running.

```python
def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### 2. Authentication Tests

Test user registration, login, token validation, and protected routes.

```python
@pytest.mark.asyncio
async def test_login(client: TestClient, db: AsyncSession):
    # Create user
    user = await create_test_user(db)

    # Test login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": user.username, "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 3. CRUD Operations

Test Create, Read, Update, Delete operations for resources.

```python
@pytest.mark.asyncio
async def test_create_resource(client: TestClient, db: AsyncSession):
    # Authentication setup
    user = await create_test_user(db)
    token = create_test_token(user.id)

    # Test create
    data = {"name": "Test Resource", "description": "Test Description"}
    response = client.post(
        "/api/v1/resources/",
        json=data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 201
    result = response.json()["data"]
    assert result["name"] == data["name"]
    assert result["description"] == data["description"]
```

### 4. Error Handling

Test how the API handles errors and edge cases.

```python
@pytest.mark.asyncio
async def test_resource_not_found(client: TestClient, db: AsyncSession):
    # Authentication setup
    user = await create_test_user(db)
    token = create_test_token(user.id)

    # Test non-existent resource
    response = client.get(
        "/api/v1/resources/999999",
        headers=get_auth_headers(token)
    )

    assert response.status_code == 404
    assert "detail" in response.json()
```

## Testing Pagination and Filtering

For endpoints that support pagination and filtering:

```python
@pytest.mark.asyncio
async def test_pagination_and_filtering(client: TestClient, db: AsyncSession):
    # Setup: Create multiple resources
    user = await create_test_user(db)
    token = create_test_token(user.id)

    # Create 20 test resources
    for i in range(20):
        await create_test_resource(db, name=f"Resource {i}")

    # Test pagination
    response = client.get(
        "/api/v1/resources/?skip=5&limit=5",
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5
    assert data["page"] == 2  # 2nd page (skip=5, limit=5)
    assert data["size"] == 5
    assert data["total"] >= 20

    # Test filtering
    response = client.get(
        "/api/v1/resources/?name=Resource%201",
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    # Should find resources with names like "Resource 1", "Resource 10"-"Resource 19"
    for item in data["data"]:
        assert "Resource 1" in item["name"]
```

## Testing File Uploads

For endpoints that handle file uploads:

```python
@pytest.mark.asyncio
async def test_file_upload(client: TestClient, db: AsyncSession):
    # Authentication setup
    user = await create_test_user(db)
    token = create_test_token(user.id)

    # Create a test file
    file_content = b"test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}

    # Test file upload
    response = client.post(
        "/api/v1/uploads/",
        files=files,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 201
    data = response.json()
    assert "filename" in data
    assert data["size"] == len(file_content)
```

## Testing Error Responses

Test validation errors and business logic errors:

```python
@pytest.mark.asyncio
async def test_validation_error(client: TestClient, db: AsyncSession):
    # Authentication setup
    user = await create_test_user(db)
    token = create_test_token(user.id)

    # Test with invalid data
    invalid_data = {"name": "", "age": -5}  # Invalid values
    response = client.post(
        "/api/v1/users/",
        json=invalid_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 422  # Validation error
    errors = response.json()
    assert "detail" in errors
```

## Best Practices

1. **Test Coverage**: Aim for high test coverage of API endpoints.
2. **Edge Cases**: Test edge cases and error scenarios, not just the happy path.
3. **Database State**: Reset database state between tests to avoid test interdependencies.
4. **Parameterized Tests**: Use pytest's parameterization for testing multiple similar cases.
5. **Test Organization**: Group related tests in the same file and use clear test names.

## Troubleshooting Common Issues

### 1. Authentication Issues

If tests involving authentication are failing:

- Verify the token generation logic in `tests/utils/helpers.py`
- Check that the token is being passed correctly in the `Authorization` header
- Ensure the user being used has the right permissions

### 2. Database Transaction Issues

If database state is not what you expect:

- Check that the database session is being properly managed
- Ensure that all database operations are awaited (async)
- Make sure the test database is being reset between tests

### 3. Async Issues

If you're getting errors related to async/await:

- Ensure that all async functions have the `@pytest.mark.asyncio` decorator
- Make sure all async calls are properly awaited
- Check that the right event loop is being used

## Example: Testing a Complete Flow

Here's an example testing a complete user flow:

```python
@pytest.mark.asyncio
async def test_user_lifecycle(client: TestClient, db: AsyncSession):
    # 1. Register a new user
    register_data = {
        "username": "lifecycle_test",
        "email": "lifecycle@example.com",
        "password": "securepassword123"
    }

    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    # 2. Get user profile
    profile_response = client.get(
        "/api/v1/users/me",
        headers=get_auth_headers(token)
    )
    assert profile_response.status_code == 200
    user_id = profile_response.json()["data"]["id"]

    # 3. Update user information
    update_data = {"full_name": "Updated Name"}
    update_response = client.put(
        f"/api/v1/users/{user_id}",
        json=update_data,
        headers=get_auth_headers(token)
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["full_name"] == "Updated Name"

    # 4. Delete user (if applicable)
    # This would require admin privileges in many systems
    # delete_response = client.delete(
    #     f"/api/v1/users/{user_id}",
    #     headers=get_auth_headers(admin_token)
    # )
    # assert delete_response.status_code == 200
```
