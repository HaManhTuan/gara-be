from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Project settings
    PROJECT_NAME: str = "FastAPI MVC Application"
    PROJECT_DESCRIPTION: str = "FastAPI application following MVC architecture with service layer"
    PROJECT_VERSION: str = "0.1.0"

    # Server settings
    SERVER_HOST: str = "0.0.0.0"  # nosec B104 - Development default
    SERVER_PORT: int = 8000
    DEBUG: bool = True

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_mvc"
    DB_ECHO: bool = False
    AUTO_CREATE_TABLES: bool = False  # Set to True to auto-create tables without migrations (development only)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False  # Set to True to enable file logging
    LOG_FILE_PATH: Optional[str] = "logs/app.log"  # File path when LOG_TO_FILE is True
    LOG_FORMAT_JSON: bool = False  # Set to True for JSON log format

    # Redis and Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Celery Worker Configuration
    CELERY_WORKER_POOL: str = "gevent"  # Pool type: gevent, prefork, threads, solo
    CELERY_WORKER_CONCURRENCY: int = 200  # Number of concurrent greenlets/processes/threads

    # Future AWS SQS Configuration (for production scalability)
    # Uncomment and configure when migrating to AWS
    # AWS_ACCESS_KEY_ID: Optional[str] = None
    # AWS_SECRET_ACCESS_KEY: Optional[str] = None
    # AWS_REGION: str = "us-east-1"
    # SQS_QUEUE_NAME: str = "celery-tasks"
    # CELERY_BROKER_URL: str = "sqs://"  # SQS broker URL
    # CELERY_BROKER_TRANSPORT_OPTIONS = {
    #     "region": AWS_REGION,
    #     "queue_name_prefix": "celery-",
    # }

    # JWT Auth
    JWT_SECRET_KEY: str = "YOUR_SECRET_KEY"  # should be overridden in .env
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Firebase Admin SDK
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None  # Path to service account JSON file
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = None  # Or JSON string in environment variable

    # Email Configuration
    SMTP_HOST: str = "mailpit"  # Use "mailpit" for Docker, "localhost" for local dev
    SMTP_PORT: int = 1025  # Mailpit SMTP port (use 587 for production SMTP)
    SMTP_USERNAME: Optional[str] = None  # Set for production SMTP servers
    SMTP_PASSWORD: Optional[str] = None  # Set for production SMTP servers
    SMTP_USE_TLS: bool = False  # Set to True for production (port 587)
    SMTP_USE_SSL: bool = False  # Set to True if using port 465
    EMAIL_FROM: str = "noreply@gara-api.com"  # Default sender email
    EMAIL_FROM_NAME: str = "Gara API"  # Default sender name
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES: int = 5  # OTP expiry time in minutes
    OTP_LENGTH: int = 6  # Length of OTP code


# Initialize settings
settings = Settings()
