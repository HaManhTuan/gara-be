# Database Migrations Guide

This guide covers database migration management using Alembic with sync database connections for reliable migration operations.

## Overview

The project uses Alembic for database migration management with **sync database connections** for reliable migration operations. A helper script is provided in `scripts/manage_migrations.py` to make migration operations easier.

## Key Features

- Uses sync database connections by default (no async complications)
- Automatically converts database URLs to sync protocol for migrations
- Clean separation between async app runtime and sync migrations
- Comprehensive logging of migration operations

## Migration Commands

```bash
# Create a new migration with auto-detection of model changes
poetry run python scripts/manage_migrations.py create -m "description"

# Apply migrations
poetry run python scripts/manage_migrations.py upgrade

# Rollback migrations
poetry run python scripts/manage_migrations.py downgrade

# Get migration history
poetry run python scripts/manage_migrations.py history

# Show current migration version
poetry run python scripts/manage_migrations.py current

# Rollback to a specific revision
poetry run python scripts/manage_migrations.py downgrade -r <revision_id>
```

## Migration Strategy

Migrations are managed using Alembic with autogenerate capability and **sync database connections** for reliability. The system automatically handles the conversion between async (app runtime) and sync (migrations) database protocols.

When you make changes to your SQLAlchemy models:

1. Create a new migration:
   ```bash
   poetry run python scripts/manage_migrations.py create -m "Description of your model changes"
   ```

2. Verify the generated migration script in `alembic/versions/`

3. Apply the migration:
   ```bash
   poetry run python scripts/manage_migrations.py upgrade
   ```

## Important Notes

- The `DATABASE_URL` in your `.env` file should use the sync protocol (`postgresql://`)
- The migration system automatically converts this to async (`postgresql+asyncpg://`) for the application runtime
- This ensures migrations run reliably without async complications

## Database Context Managers

The project provides both sync and async context managers for database operations, plus a FastAPI dependency:

### FastAPI Dependency (Recommended for Controllers)

For FastAPI route handlers, use the dependency injection:

```python
from fastapi import Depends
from app.config.database import get_db
from app.models.user import User
from sqlalchemy import select

@app.get("/users/")
async def get_users(db = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Sync Context Manager

For operations that need sync database access outside of FastAPI's async context:

```python
from app.config.database import get_sync_db
from app.models.user import User

# Using the sync context manager
with get_sync_db() as db:
    # Perform sync database operations
    users = db.query(User).all()
    new_user = User(username="test", email="test@example.com", password="password")
    db.add(new_user)
    db.commit()
```

### Async Context Manager

For async operations outside of FastAPI's dependency injection:

```python
from app.config.database import get_async_db
from app.models.user import User
from sqlalchemy import select

# Using the async context manager
async with get_async_db() as db:
    # Perform async database operations
    result = await db.execute(select(User))
    users = result.scalars().all()
    new_user = User(username="test", email="test@example.com", password="password")
    db.add(new_user)
    await db.commit()
```

## Migration Best Practices

1. **Always review generated migrations** before applying them
2. **Test migrations on a copy of production data** when possible
3. **Use descriptive migration messages** to document changes
4. **Backup your database** before applying migrations in production
5. **Apply migrations in a maintenance window** for production systems

## Troubleshooting

### Common Issues

1. **Greenlet errors**: Ensure you're using sync connections for migrations
2. **Connection errors**: Verify your `DATABASE_URL` is correct
3. **Migration conflicts**: Use `alembic merge` to resolve conflicts

### Getting Help

- Check the migration history: `poetry run python scripts/manage_migrations.py history`
- View current state: `poetry run python scripts/manage_migrations.py current`
- Review migration files in `alembic/versions/`
