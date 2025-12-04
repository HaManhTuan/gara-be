# Testing Framework for FastAPI MVC Project

This directory contains the testing framework for the FastAPI MVC project, focusing on API testing.

## Directory Structure

- `tests/`: Main test directory
  - `api/`: API tests
  - `utils/`: Test utilities and helpers
  - `conftest.py`: Test configuration and fixtures

## Running Tests

### Using Poetry

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/api/test_health.py

# Run tests with specific marker
poetry run pytest -m api
```

### Using the run_tests.py Script

```bash
# Run all tests
poetry run python scripts/run_tests.py

# Run tests with coverage
poetry run python scripts/run_tests.py --coverage

# Generate HTML coverage report
poetry run python scripts/run_tests.py --coverage --html

# Run only API tests
poetry run python scripts/run_tests.py --api-only

# Run specific test file
poetry run python scripts/run_tests.py tests/api/test_health.py
```

### Using Docker Compose for Testing

The `docker-compose.test.yml` file provides a PostgreSQL database specifically for testing.

```bash
# Start the test database
docker-compose -f docker-compose.test.yml up -d

# Run tests against the test database
APP_ENV=test DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/fastapi_mvc_test poetry run pytest

# Stop the test database
docker-compose -f docker-compose.test.yml down
```

## Test Database

Tests use SQLite in-memory database by default for simplicity and speed.
If you need to test with PostgreSQL, use the Docker Compose setup mentioned above.

### SQLite Configuration

The SQLite in-memory database uses a named database with shared cache to ensure connections work properly:
```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:mem_db?mode=memory&cache=shared&uri=true"
```

This configuration allows multiple connections to access the same in-memory database during a test session.

### Database Migration for Tests

Unlike the main application which uses Alembic for migrations, tests use SQLAlchemy's metadata system to create tables directly:

1. A session-scoped fixture `setup_test_db` runs once before all tests to create all tables
2. All models are explicitly imported in conftest.py to ensure they're registered with the metadata
3. Transactions are used to isolate test cases and ensure clean state

This approach provides faster test execution and simpler setup than running migrations for each test.

## Troubleshooting

### "No such table" Errors

If you encounter "no such table" errors:

1. Make sure all models are properly imported in `conftest.py`
2. Check that the database URL is correct and accessible
3. Ensure that the `setup_test_db` fixture runs before your tests
4. Try running with `--no-cov` to eliminate coverage-related issues

### Connection Issues

For SQLite connection issues:

1. Ensure the connection URL uses `?mode=memory&cache=shared&uri=true`
2. Check that `check_same_thread=False` is in connect_args
3. Make sure your tests properly await async operations

## Writing New Tests

### API Tests

Place API tests in the `tests/api/` directory with filenames starting with `test_`.

All tests should follow the AAA (Arrange-Act-Assert) pattern:

```python
@pytest.mark.asyncio
async def test_some_api_endpoint(client: TestClient, db: AsyncSession):
    # Arrange - Set up test data and conditions
    user = await create_test_user(db, email="test@example.com", password="password123")
    token = create_test_token(user.id)

    # Act - Execute the code being tested
    response = client.get(
        "/some-endpoint",
        headers=get_auth_headers(token)
    )

    # Assert - Verify that the results are as expected
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

The AAA pattern makes tests more readable and maintainable:
- **Arrange**: Set up the test data and conditions
- **Act**: Execute the code or function being tested
- **Assert**: Verify that the results are as expected

### Fixtures

Common test fixtures are defined in `conftest.py`. Use these fixtures in your tests:

- `client`: FastAPI test client for synchronous testing
- `async_client`: FastAPI test client for asynchronous testing
- `app`: FastAPI application instance
- `db`: SQLAlchemy AsyncSession for database access
- `setup_test_db`: Session-scoped fixture that runs once to set up the test database

### Utility Functions

The `tests/utils/helpers.py` file contains utility functions for testing:

- `create_test_user()`: Create a test user in the database
- `create_test_token()`: Create a JWT token for testing
- `get_auth_headers()`: Get authorization headers with a token
