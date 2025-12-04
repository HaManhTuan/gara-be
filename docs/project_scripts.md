# Project Scripts Guide

This guide covers all utility scripts available in the `scripts/` directory for project management and development tasks.

## Available Scripts

### 1. `manage_migrations.py`

Helper script for managing Alembic migrations with **sync database connections**:

```bash
# Usage
poetry run python scripts/manage_migrations.py [command] [options]

# Commands:
# - create: Create a new migration
# - upgrade: Apply migrations
# - downgrade: Rollback migrations
# - history: View migration history
# - current: Show current migration version
```

**Key Features:**
- Uses sync database connections by default for reliable migrations
- Automatically handles database URL conversion (sync for migrations, async for app)
- Comprehensive logging of migration operations
- No async complications or greenlet errors

**Examples:**
```bash
# Create a new migration
poetry run python scripts/manage_migrations.py create -m "Add user table"

# Apply all pending migrations
poetry run python scripts/manage_migrations.py upgrade

# Rollback last migration
poetry run python scripts/manage_migrations.py downgrade

# Rollback to specific revision
poetry run python scripts/manage_migrations.py downgrade -r abc123

# View migration history
poetry run python scripts/manage_migrations.py history

# Check current migration version
poetry run python scripts/manage_migrations.py current
```

### 2. `init_db.py`

Initializes the database with tables and seed data:

```bash
poetry run python scripts/init_db.py
```

**What it does:**
- Creates all database tables
- Inserts initial/seed data
- Useful for setting up a fresh database

### 3. `run_tests.py`

Runs the test suite with proper configuration:

```bash
poetry run python scripts/run_tests.py
```

**Features:**
- Configures test environment
- Runs all tests with proper database setup
- Generates coverage reports
- Handles test database cleanup

### 4. `start_worker.py`

Starts the Celery worker for background tasks:

```bash
poetry run python scripts/start_worker.py
```

**Features:**
- Starts Celery worker with proper configuration
- Handles worker lifecycle management
- Configures logging for workers

### 5. `check_table_models.py`

Utility script to check database table models:

```bash
poetry run python scripts/check_table_models.py
```

**Purpose:**
- Validates model definitions
- Checks database schema consistency
- Useful for debugging model issues

### 6. `test_sqlite_async.py`

Tests SQLite async functionality:

```bash
poetry run python scripts/test_sqlite_async.py
```

**Purpose:**
- Tests async SQLite operations
- Validates async database functionality
- Useful for development and testing

## Script Development Guidelines

### Creating New Scripts

When creating new utility scripts, follow these guidelines:

1. **Use proper imports:**
   ```python
   import sys
   from pathlib import Path

   # Add parent directory to path
   sys.path.append(str(Path(__file__).parent.parent))
   ```

2. **Include logging:**
   ```python
   from app.utils.logger import get_logger
   logger = get_logger(__name__)
   ```

3. **Handle errors gracefully:**
   ```python
   try:
       # Your code here
   except Exception as e:
       logger.error(f"Operation failed: {e}")
       sys.exit(1)
   ```

4. **Add help/usage information:**
   ```python
   import argparse

   parser = argparse.ArgumentParser(description="Script description")
   parser.add_argument("--option", help="Option description")
   ```

### Script Categories

**Database Scripts:**
- `manage_migrations.py` - Migration management
- `init_db.py` - Database initialization
- `check_table_models.py` - Model validation

**Testing Scripts:**
- `run_tests.py` - Test execution
- `test_sqlite_async.py` - Async testing

**Worker Scripts:**
- `start_worker.py` - Celery worker management

## Common Script Patterns

### Database Connection Pattern

For scripts that need database access:

```python
from app.config.database import get_sync_db, get_async_db

# For sync operations
with get_sync_db() as db:
    # Database operations
    pass

# For async operations
async with get_async_db() as db:
    # Async database operations
    pass
```

### Logging Pattern

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting script execution")
    try:
        # Your logic here
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise
```

### Argument Parsing Pattern

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--input", help="Input file path")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")

    # Use args.input, args.output, etc.
```

## Troubleshooting Scripts

### Common Issues

1. **Import errors**: Ensure the script adds the parent directory to `sys.path`
2. **Database connection errors**: Check environment variables and database availability
3. **Permission errors**: Ensure proper file permissions for log files and database access

### Debugging Tips

1. **Enable verbose logging**: Use `--verbose` flag if available
2. **Check environment**: Verify `.env` file is properly configured
3. **Test database connection**: Use `check_table_models.py` to validate database setup
4. **Review logs**: Check log files for detailed error information

## Script Maintenance

### Regular Tasks

1. **Update dependencies**: Keep script dependencies up to date
2. **Test scripts**: Run scripts regularly to ensure they work
3. **Update documentation**: Keep this guide updated when scripts change
4. **Review error handling**: Ensure scripts handle errors gracefully

### Best Practices

1. **Keep scripts focused**: Each script should have a single, clear purpose
2. **Use consistent patterns**: Follow established patterns for new scripts
3. **Include help text**: Always provide usage information
4. **Handle edge cases**: Consider error conditions and edge cases
5. **Test thoroughly**: Test scripts in different environments
