# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used in the FastAPI MVC application.

## Configuration Overview

The application uses Pydantic Settings to manage configuration through environment variables. Default values are provided in `app/config/settings.py`, and can be overridden in a `.env` file.

## Environment Variables Table

| Variable                      | Description                               | Default Value                                      |
|-------------------------------|-------------------------------------------|---------------------------------------------------|
| SERVER_HOST                   | Host to bind the server to                | 0.0.0.0                                            |
| SERVER_PORT                   | Port to bind the server to                | 8000                                               |
| DEBUG                         | Enable debug mode                         | True                                               |
| PROJECT_NAME                  | Name of the project                       | "FastAPI MVC Application"                          |
| PROJECT_DESCRIPTION           | Description of the project                | "FastAPI application following MVC architecture..." |
| PROJECT_VERSION               | Version of the project                    | "0.1.0"                                            |
| DATABASE_URL                  | Database connection URL (sync protocol)  | postgresql://postgres:postgres@localhost:5432/fastapi_mvc |
| DB_ECHO                       | Echo SQL statements                       | False                                              |
| AUTO_CREATE_TABLES            | Auto create tables on startup             | False                                              |
| LOG_LEVEL                     | Logging level                             | INFO                                               |
| LOG_FORMAT                    | Logging format                            | "{time:YYYY-MM-DD HH:mm:ss} \| {level} \| {message}" |
| LOG_FILE_PATH                 | Path to log file                          | logs/app.log                                       |
| REDIS_HOST                    | Redis host                                | localhost                                          |
| REDIS_PORT                    | Redis port                                | 6379                                               |
| REDIS_DB                      | Redis database                            | 0                                                  |
| CELERY_BROKER_URL             | Celery broker URL                         | redis://localhost:6379/0                           |
| CELERY_RESULT_BACKEND         | Celery result backend                     | redis://localhost:6379/0                           |
| JWT_SECRET_KEY                | Secret key for JWT                        | change_this_to_a_secure_secret                     |
| JWT_ALGORITHM                 | Algorithm for JWT                         | HS256                                              |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration time in minutes    | 30                                                 |

## Configuration Categories

### Server Configuration

- **SERVER_HOST**: The host address to bind the server to. Use `0.0.0.0` for external access.
- **SERVER_PORT**: The port number for the server. Default is 8000.
- **DEBUG**: Enable or disable debug mode. Set to `False` in production.

### Project Information

- **PROJECT_NAME**: Display name for the project.
- **PROJECT_DESCRIPTION**: Description shown in API documentation.
- **PROJECT_VERSION**: Version number for the project.

### Database Configuration

- **DATABASE_URL**: Connection string for the database. Should use sync protocol (`postgresql://`) for migrations.
- **DB_ECHO**: Enable SQL statement logging for debugging.
- **AUTO_CREATE_TABLES**: Automatically create tables on startup (development only).

### Logging Configuration

- **LOG_LEVEL**: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- **LOG_FORMAT**: Customize the log message format.
- **LOG_FILE_PATH**: Specify where to write log files.

### Redis Configuration

- **REDIS_HOST**: Redis server hostname.
- **REDIS_PORT**: Redis server port.
- **REDIS_DB**: Redis database number.

### Celery Configuration

- **CELERY_BROKER_URL**: URL for the Celery message broker.
- **CELERY_RESULT_BACKEND**: URL for storing Celery task results.

### JWT Authentication

- **JWT_SECRET_KEY**: Secret key for signing JWT tokens. **Must be changed in production.**
- **JWT_ALGORITHM**: Algorithm used for JWT signing.
- **JWT_ACCESS_TOKEN_EXPIRE_MINUTES**: Token expiration time in minutes.

## Environment Setup

### Development Environment

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

### Production Environment

For production deployment:

1. Set `DEBUG=False`
2. Use a strong `JWT_SECRET_KEY`
3. Configure proper database credentials
4. Set appropriate `LOG_LEVEL`
5. Use production Redis and database URLs

### Docker Environment

When using Docker Compose, environment variables can be set in:

1. `.env` file (for docker-compose)
2. `docker-compose.yml` environment section
3. Docker environment files

## Security Considerations

### Required Changes for Production

1. **JWT_SECRET_KEY**: Generate a strong, random secret key
2. **DEBUG**: Set to `False`
3. **Database credentials**: Use strong passwords
4. **Redis**: Configure authentication if needed

### Example Production .env

```bash
DEBUG=False
JWT_SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@db-host:5432/production_db
REDIS_HOST=redis-host
CELERY_BROKER_URL=redis://redis-host:6379/0
LOG_LEVEL=WARNING
```

## Environment-Specific Configurations

### Development

```bash
DEBUG=True
LOG_LEVEL=DEBUG
DB_ECHO=True
```

### Testing

```bash
DEBUG=True
DATABASE_URL=sqlite+aiosqlite:///file:mem_db?mode=memory&cache=shared&uri=true
LOG_LEVEL=DEBUG
```

### Production

```bash
DEBUG=False
LOG_LEVEL=INFO
DB_ECHO=False
```

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check `DATABASE_URL` format and credentials
2. **Redis connection errors**: Verify `REDIS_HOST` and `REDIS_PORT`
3. **JWT errors**: Ensure `JWT_SECRET_KEY` is set
4. **Logging issues**: Check `LOG_FILE_PATH` permissions

### Validation

The application validates all environment variables on startup. Check the logs for any validation errors.
