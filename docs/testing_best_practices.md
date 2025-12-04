# Testing Best Practices

This document outlines the best practices for writing and maintaining tests in the FastAPI MVC project.

## AAA Pattern

All tests should follow the AAA (Arrange-Act-Assert) pattern, which makes tests more readable and maintainable:

### Arrange

The "Arrange" section prepares everything for the test:
- Create test data
- Set up test dependencies
- Configure test conditions

```python
# Arrange
user = await create_test_user(
    db,
    email="test@example.com",
    password="password123",
    is_admin=True
)

token = create_test_token(user.id)
```

### Act

The "Act" section executes the code being tested:
- Call the function or endpoint
- Trigger the behavior being tested

```python
# Act
response = client.post(
    "/api/v1/users/",
    json=user_data,
    headers=get_auth_headers(token)
)
```

### Assert

The "Assert" section verifies the results:
- Check that the function returned the expected values
- Verify that the correct changes were made
- Ensure error cases are handled correctly

```python
# Assert
assert response.status_code == status.HTTP_201_CREATED
data = response.json()
assert data["data"]["email"] == user_data["email"]
assert "password" not in data["data"]  # Password should not be returned
```

## General Testing Guidelines

### 1. Test Independence

Each test should be independent of other tests. Tests should not depend on the state created by other tests.

```python
# Good - Test is self-contained
async def test_create_user(client, db):
    # Arrange - Create all needed test data here
    # Act - Execute the test
    # Assert - Verify the results
```

### 2. Clear Test Names

Test names should clearly describe what they're testing:

```python
# Good - Clear name
async def test_login_with_invalid_password_returns_401()

# Bad - Unclear name
async def test_login_scenario_2()
```

### 3. One Assertion Concept Per Test

Each test should focus on verifying one concept or behavior:

```python
# Good - Tests one concept
async def test_user_creation_returns_201_status()
async def test_user_creation_returns_user_data_without_password()

# Bad - Tests multiple concepts
async def test_user_creation_works_correctly()
```

### 4. Use Fixtures for Common Setup

Use pytest fixtures for common setup code:

```python
@pytest.fixture
async def authenticated_user(db):
    user = await create_test_user(db)
    token = create_test_token(user.id)
    return {"user": user, "token": token}

async def test_protected_endpoint(client, authenticated_user):
    # Use authenticated_user.user and authenticated_user.token
```

### 5. Test Edge Cases

Don't just test the happy path; test edge cases:

```python
async def test_login_with_non_existent_user()
async def test_create_user_with_duplicate_email()
async def test_update_user_with_empty_data()
```

### 6. Keep Tests Fast

Tests should be fast to encourage frequent running:

- Use in-memory databases when possible
- Mock external services
- Avoid unnecessary setup

### 7. Isolate Integration and Unit Tests

Use markers to separate different types of tests:

```python
@pytest.mark.unit
def test_password_hashing()

@pytest.mark.integration
async def test_database_connection()

@pytest.mark.api
async def test_user_endpoint()
```

## API Testing Specific Practices

### 1. Test Status Codes

Always verify the HTTP status code:

```python
assert response.status_code == status.HTTP_200_OK
```

### 2. Test Response Structure

Verify the structure of the response:

```python
data = response.json()
assert "data" in data
assert "meta" in data
assert isinstance(data["data"], list)
```

### 3. Test Permissions

Verify that authorization works correctly:

```python
# Test with no auth
response = client.get("/protected-endpoint")
assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Test with incorrect permissions
response = client.get("/admin-endpoint", headers=get_auth_headers(non_admin_token))
assert response.status_code == status.HTTP_403_FORBIDDEN
```

### 4. Test Error Responses

Verify that error responses include appropriate details:

```python
response = client.post("/api/v1/users/", json=invalid_data)
assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
data = response.json()
assert "detail" in data
```

## Example Test Following Best Practices

```python
@pytest.mark.api
@pytest.mark.asyncio
async def test_update_user_name(client: TestClient, db: AsyncSession):
    """
    Test that an authenticated user can update their name.
    """
    # Arrange
    user = await create_test_user(
        db,
        email="update-test@example.com",
        password="password123",
        username="update-test"
    )

    token = create_test_token(user.id)
    update_data = {"full_name": "Updated Name"}

    # Act
    response = client.put(
        f"/api/v1/users/{user.id}",
        json=update_data,
        headers=get_auth_headers(token)
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["id"] == user.id
    assert data["data"]["full_name"] == "Updated Name"
```
