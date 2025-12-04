# Deployment Guide

This guide covers deployment strategies, production considerations, and operational best practices for the FastAPI MVC application.

## Deployment Options

### 1. Docker Deployment (Recommended)

The project includes comprehensive Docker configuration for easy deployment and development.

#### Prerequisites
- Docker and Docker Compose installed on your system
- At least 4GB RAM available for containers
- Ports 8000, 5432, and 6379 available

#### Quick Start with Docker

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - FastAPI application on port 8000
   - PostgreSQL database on port 5432
   - Redis on port 6379
   - Celery worker

2. **Run in detached mode:**
   ```bash
   docker-compose up -d
   ```

3. **Stop all services:**
   ```bash
   docker-compose down
   ```

#### Docker Services

**Application Service:**
- FastAPI application
- Automatic database migration on startup
- Health checks and monitoring
- Log aggregation

**Database Service:**
- PostgreSQL 15
- Persistent data storage
- Connection pooling
- Backup capabilities

**Redis Service:**
- Session storage
- Celery broker
- Caching layer
- Task queue management

**Worker Service:**
- Celery background workers
- Task processing
- Error handling and retries
- Monitoring and logging

#### Accessing Services

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: PostgreSQL on localhost:5432
  - User: postgres
  - Password: postgres
  - Database: fastapi_mvc
- **Redis**: localhost:6379

### 2. Manual Deployment

#### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Poetry package manager

#### Production Setup

1. **Install dependencies:**
   ```bash
   poetry install --no-dev
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.prod
   # Edit production configuration
   ```

3. **Set up database:**
   ```bash
   # Create production database
   createdb fastapi_mvc_prod

   # Apply migrations
   poetry run python scripts/manage_migrations.py upgrade
   ```

4. **Start services:**
   ```bash
   # Start API server
   poetry run uvicorn main:app --host 0.0.0.0 --port 8000

   # Start Celery worker
   poetry run celery -A app.workers.celery_worker worker --loglevel=info

   # Start scheduler
   poetry run python -m app.jobs.scheduler
   ```

### 3. Cloud Deployment

#### AWS Deployment

**Using ECS with Fargate:**
1. Create ECS cluster
2. Define task definitions for app and worker
3. Set up RDS for PostgreSQL
4. Configure ElastiCache for Redis
5. Use Application Load Balancer for routing

**Using EC2:**
1. Launch EC2 instances
2. Install Docker and Docker Compose
3. Configure security groups
4. Set up RDS and ElastiCache
5. Deploy using Docker Compose

#### Google Cloud Platform

**Using Cloud Run:**
1. Containerize the application
2. Deploy to Cloud Run
3. Use Cloud SQL for PostgreSQL
4. Use Memorystore for Redis
5. Configure load balancing

#### Azure Deployment

**Using Container Instances:**
1. Create container group
2. Deploy application containers
3. Use Azure Database for PostgreSQL
4. Use Azure Cache for Redis
5. Configure Application Gateway

## Production Configuration

### Environment Variables

Create a production `.env` file with the following settings:

```bash
# Production settings
DEBUG=False
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/production_db

# Redis
REDIS_HOST=redis-host
CELERY_BROKER_URL=redis://redis-host:6379/0

# Security
JWT_SECRET_KEY=your-super-secret-production-key

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Security Considerations

#### Required Security Changes

1. **JWT Secret Key:**
   ```bash
   # Generate a strong secret key
   JWT_SECRET_KEY=$(openssl rand -base64 32)
   ```

2. **Database Security:**
   - Use strong passwords
   - Enable SSL connections
   - Restrict network access
   - Regular security updates

3. **Application Security:**
   - Set `DEBUG=False`
   - Use HTTPS in production
   - Configure proper CORS settings
   - Implement rate limiting

4. **Infrastructure Security:**
   - Use VPCs and security groups
   - Enable firewall rules
   - Regular security patches
   - Monitor access logs

### Performance Optimization

#### Database Optimization

1. **Connection Pooling:**
   ```python
   # Configure connection pool
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

2. **Query Optimization:**
   - Use database indexes
   - Optimize N+1 queries
   - Implement query caching
   - Use database monitoring

3. **Database Scaling:**
   - Read replicas for read-heavy workloads
   - Database sharding for large datasets
   - Connection pooling
   - Query optimization

#### Application Optimization

1. **Caching Strategy:**
   - Redis for session storage
   - Application-level caching
   - CDN for static assets
   - Database query caching

2. **Load Balancing:**
   - Multiple application instances
   - Health checks
   - Session affinity
   - Auto-scaling

3. **Monitoring:**
   - Application performance monitoring
   - Database monitoring
   - Error tracking
   - Log aggregation

## Monitoring and Logging

### Application Monitoring

#### Health Checks

The application provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

#### Metrics Collection

1. **Application Metrics:**
   - Request/response times
   - Error rates
   - Throughput
   - Resource utilization

2. **Database Metrics:**
   - Connection pool usage
   - Query performance
   - Lock contention
   - Storage usage

3. **Infrastructure Metrics:**
   - CPU and memory usage
   - Network I/O
   - Disk usage
   - Container health

### Logging Strategy

#### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for handled exceptions
- **CRITICAL**: Critical errors that may cause application failure

#### Log Aggregation

1. **Centralized Logging:**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Fluentd for log collection
   - CloudWatch for AWS deployments
   - Stackdriver for GCP deployments

2. **Log Rotation:**
   - Automatic log rotation
   - Log compression
   - Retention policies
   - Storage optimization

## Backup and Recovery

### Database Backup

#### Automated Backups

1. **Daily Backups:**
   ```bash
   # Create backup script
   pg_dump -h db-host -U user -d database > backup_$(date +%Y%m%d).sql
   ```

2. **Backup Storage:**
   - Cloud storage (S3, GCS, Azure Blob)
   - Encrypted backups
   - Cross-region replication
   - Retention policies

#### Recovery Procedures

1. **Point-in-Time Recovery:**
   - WAL archiving
   - Continuous backup
   - Recovery testing
   - RTO/RPO planning

2. **Disaster Recovery:**
   - Multi-region deployment
   - Backup verification
   - Recovery testing
   - Documentation

### Application Backup

1. **Configuration Backup:**
   - Environment variables
   - Application configuration
   - Infrastructure as Code
   - Version control

2. **Code Backup:**
   - Git repositories
   - Container images
   - Deployment scripts
   - Documentation

## Scaling Strategies

### Horizontal Scaling

#### Load Balancing

1. **Application Load Balancer:**
   - Multiple application instances
   - Health checks
   - Session affinity
   - SSL termination

2. **Database Load Balancing:**
   - Read replicas
   - Connection pooling
   - Query routing
   - Failover handling

#### Auto-scaling

1. **Container Auto-scaling:**
   - CPU and memory thresholds
   - Request-based scaling
   - Predictive scaling
   - Cost optimization

2. **Database Scaling:**
   - Read replica scaling
   - Storage scaling
   - Performance monitoring
   - Capacity planning

### Vertical Scaling

1. **Resource Optimization:**
   - CPU and memory upgrades
   - Storage optimization
   - Network optimization
   - Performance tuning

2. **Application Optimization:**
   - Code optimization
   - Algorithm improvements
   - Caching strategies
   - Database optimization

## Maintenance and Updates

### Deployment Pipeline

1. **CI/CD Pipeline:**
   - Automated testing
   - Code quality checks
   - Security scanning
   - Automated deployment

2. **Blue-Green Deployment:**
   - Zero-downtime deployments
   - Rollback capabilities
   - Health checks
   - Traffic switching

### Update Procedures

1. **Application Updates:**
   - Version control
   - Testing procedures
   - Rollback plans
   - Monitoring

2. **Infrastructure Updates:**
   - Security patches
   - OS updates
   - Dependency updates
   - Configuration changes

### Maintenance Windows

1. **Scheduled Maintenance:**
   - Database maintenance
   - System updates
   - Security patches
   - Performance optimization

2. **Emergency Procedures:**
   - Incident response
   - Rollback procedures
   - Communication plans
   - Post-incident reviews

This deployment guide provides comprehensive information for deploying and maintaining the FastAPI MVC application in production environments.
