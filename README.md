# FastAPI MVC Application

A modern FastAPI application following MVC architecture with service layer, featuring async database operations, comprehensive logging, background workers, and Docker support.

## Quick Start

### Prerequisites

- Python 3.9+
- Poetry
- PostgreSQL
- Redis (for Celery workers)
- Docker & Docker Compose (optional)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd baseFastApiMVC
   poetry install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up database:**
   ```bash
   # Create PostgreSQL database
   createdb fastapi_mvc

   # Apply migrations
   poetry run python scripts/manage_migrations.py upgrade
   ```

4. **Run the application:**
   ```bash
   # Start API server
   poetry run uvicorn main:app --reload

   # Start Celery worker (in another terminal)
   poetry run celery -A app.workers.celery_worker worker --loglevel=info

   # Start scheduler (in another terminal)
   poetry run python -m app.jobs.scheduler
   ```

### Docker Setup (Alternative)

```bash
# Start all services with Docker
docker-compose up --build

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Project Structure

```
baseFastApiMVC/
├── app/
│   ├── config/         # Configuration and settings
│   ├── controllers/    # API route handlers
│   ├── models/         # Database models
│   ├── services/       # Business logic layer
│   ├── repositories/   # Data access layer
│   ├── schemas/        # Pydantic models
│   ├── middlewares/    # Custom middleware
│   ├── utils/          # Utility functions
│   ├── workers/        # Background workers
│   └── jobs/           # Scheduled jobs
├── tests/              # Test suite
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
├── docs/               # Documentation
└── main.py             # Application entry point
```

## Key Features

- **MVC Architecture** with service layer
- **Async Database Operations** with sync migrations
- **Comprehensive Logging** system
- **Background Workers** with Celery
- **Scheduled Tasks** with APScheduler
- **Docker Support** with PostgreSQL
- **Database Migrations** with Alembic
- **API Documentation** with Swagger/ReDoc

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/api/test_health.py
```

## Common Commands

```bash
# Database migrations
poetry run python scripts/manage_migrations.py upgrade
poetry run python scripts/manage_migrations.py create -m "description"

# Run tests
poetry run python scripts/run_tests.py

# Initialize database
poetry run python scripts/init_db.py

# Code quality (pre-commit)
poetry run pre-commit run --all-files
poetry run pre-commit install
```

## Documentation

For detailed information, see the documentation in the `docs/` folder:

### Development Guides
- **[Development Guide](docs/development-guide.md)** - Complete guide for adding new features with base service and repository
- **[Quick Reference](docs/quick-reference.md)** - Templates and patterns for CRUD operations

### Architecture & Patterns
- [Architecture](docs/architecture.md) - System architecture and design patterns
- [Models Guide](docs/models_guide.md) - Database models guide
- [Repositories Guide](docs/repositories_guide.md) - Repository pattern guide
- [Services Guide](docs/services_guide.md) - Service layer guide
- [Controllers Guide](docs/controllers_guide.md) - API controllers guide

### Operations & Deployment
- [Database Migrations](docs/database_migrations.md) - Complete migration guide
- [Environment Variables](docs/environment_variables.md) - Configuration reference
- [Project Scripts](docs/project_scripts.md) - Utility scripts guide
- [Deployment](docs/deployment.md) - Production deployment guide

### Testing & Quality
- [API Testing Guide](docs/api_testing_guide.md) - Testing best practices
- [Pre-commit Setup](docs/pre_commit_setup.md) - Code quality and pre-commit hooks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
