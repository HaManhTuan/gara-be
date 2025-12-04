# Celery Workers Guide

## Overview

This application uses Celery with gevent pool for processing background tasks. The gevent pool is optimized for IO-intensive operations, making it ideal for tasks that involve database queries, external API calls, file operations, and other IO-bound work.

## Architecture

### Worker Pool: Gevent

**Gevent** is a coroutine-based Python networking library that uses greenlets to provide high-level synchronous API. In our Celery setup:

- **Concurrency Model**: Greenlets (lightweight coroutines)
- **Best For**: IO-intensive tasks
- **Memory**: Lower memory footprint than prefork
- **Scalability**: Can handle thousands of concurrent greenlets

### Why Gevent Over Prefork?

| Feature | Prefork | Gevent |
|---------|---------|--------|
| **Concurrency Model** | Processes | Greenlets |
| **Memory Usage** | High (each process) | Low (shared process) |
| **Best For** | CPU-intensive | IO-intensive |
| **Startup Time** | Slower | Faster |
| **Scaling** | Limited by CPU cores | Limited by memory |
| **Code Execution** | Sync only | Sync + Async (with wrapper) |

For our application with primarily IO tasks (database queries, API calls), gevent provides better performance and resource utilization.

## Async/Await Integration

Our tasks use async/await patterns for better code reuse between FastAPI endpoints and Celery workers.

### Architecture

```python
# 1. Define async helper function (reusable)
async def get_user_info_async(user_id: str) -> dict:
    async with get_async_db() as db:
        user = await user_repository.get_by_id(db, user_id)
        return {"user": user}

# 2. Create Celery task that wraps async function
@celery_app.task(name="get_user_info")
def get_user_info(user_id: str) -> dict:
    return run_async(get_user_info_async(user_id))
```

### Async Wrapper (`run_async`)

The `run_async` utility bridges gevent's greenlet world with Python's asyncio:

```python
from app.workers.async_task import run_async

def run_async(coro: Coroutine) -> Any:
    """Run async coroutine in gevent context"""
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)
```

**Benefits**:
- Reuse async service/repository code in Celery tasks
- Share business logic between FastAPI and workers
- Maintain type safety with async/await

## Task Development

### Creating a New Task

1. **Define async helper function**:

```python
async def process_order_async(order_id: str) -> dict:
    """Async business logic - can be reused in FastAPI endpoints"""
    logger.info(f"Processing order {order_id}")

    # Use async repository
    async with get_async_db() as db:
        order = await order_repository.get_by_id(db, order_id)

        # External API call
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.payment.com/charge", ...)

        return {"status": "success"}
```

2. **Create Celery task wrapper**:

```python
@celery_app.task(name="process_order")
def process_order(order_id: str) -> dict:
    """Celery task that runs async function"""
    return run_async(process_order_async(order_id))
```

3. **Call from FastAPI endpoint** (reusing same logic):

```python
@router.post("/orders/{order_id}/process")
async def process_order_endpoint(order_id: str):
    """Same logic as Celery task"""
    result = await process_order_async(order_id)
    return ResponseBuilder.success(data=result)
```

### Task with Retry

```python
@celery_app.task(name="send_email", bind=True, max_retries=3)
def send_email(self: Task, recipient: str, message: str) -> dict:
    """Task with retry on failure"""
    try:
        return run_async(send_email_async(recipient, message))
    except Exception as exc:
        logger.error(f"Failed to send email: {str(exc)}")
        retry_in = 60 * (2**self.request.retries)  # Exponential backoff
        raise self.retry(exc=exc, countdown=retry_in)
```

## Configuration

### Worker Settings

Located in `app/config/settings.py`:

```python
CELERY_WORKER_POOL: str = "gevent"
CELERY_WORKER_CONCURRENCY: int = 200
```

### Celery Configuration

Located in `app/workers/celery_app.py`:

```python
celery_app.conf.update(
    worker_prefetch_multiplier=1,      # One task at a time
    task_acks_late=True,                # Ack after completion
    worker_max_tasks_per_child=1000,   # Restart after N tasks
    worker_max_memory_per_child=200000, # Restart if >200MB
)
```

## Running Workers

### Local Development

```bash
# Start worker with default concurrency (200)
poetry run python scripts/start_worker.py

# Custom concurrency
poetry run python scripts/start_worker.py --concurrency=500
```

### Docker

```bash
docker-compose up celery_worker
```

Worker starts with: `--pool=gevent --concurrency=200`

### Direct Celery Command

```bash
poetry run celery -A app.workers.celery_app worker \
    --pool=gevent \
    --concurrency=200 \
    --loglevel=info
```

## Monitoring

### Check Worker Status

```bash
poetry run celery -A app.workers.celery_app inspect active
```

### View Task Results

```bash
poetry run celery -A app.workers.celery_app result <task_id>
```

### Flower (Web UI)

Install Flower for web-based monitoring:

```bash
poetry add flower
poetry run celery -A app.workers.celery_app flower
```

Access at: http://localhost:5555

## Performance Tuning

### Concurrency

Adjust based on workload:

- **Low IO**: 50-100 greenlets
- **Medium IO**: 200-300 greenlets
- **High IO**: 500-1000 greenlets

Monitor memory usage and adjust accordingly.

### Task Prefetching

```python
worker_prefetch_multiplier=1  # Recommended for IO tasks
```

Set to 1 to ensure tasks are distributed evenly across workers.

### Memory Management

```python
worker_max_tasks_per_child=1000
worker_max_memory_per_child=200000
```

Prevents memory leaks by restarting workers periodically.

## Best Practices

### 1. Always Use Async for IO Operations

✅ **Good**:
```python
async def fetch_data():
    async with httpx.AsyncClient() as client:
        return await client.get("...")
```

❌ **Bad** (blocks gevent):
```python
def fetch_data():
    return requests.get("...")  # Blocks greenlet
```

### 2. Reuse Async Code

✅ **Good**:
```python
# Shared async function
async def process_payment(order_id):
    ...

# Used in both Celery and FastAPI
@celery_app.task
def process_payment_task(order_id):
    return run_async(process_payment(order_id))

@router.post("/payments/{order_id}")
async def process_payment_endpoint(order_id):
    return await process_payment(order_id)
```

### 3. Handle Exceptions Gracefully

```python
@celery_app.task(bind=True, max_retries=3)
def my_task(self, data):
    try:
        return run_async(process_async(data))
    except TransientError as e:
        raise self.retry(exc=e, countdown=60)
    except PermanentError as e:
        # Don't retry, log and fail
        logger.error(f"Permanent error: {e}")
        return {"status": "failed"}
```

### 4. Monitor Performance

Use logging to track task duration:

```python
@celery_app.task(name="slow_task")
def slow_task(data):
    start_time = time.time()
    result = run_async(process_async(data))
    duration = time.time() - start_time
    logger.info(f"Task completed in {duration:.2f}s")
    return result
```

## Migration from Prefork

If you have existing tasks using prefork:

1. **Keep existing tasks unchanged** - they'll still work
2. **Add new gevent-optimized tasks** alongside
3. **Gradually migrate** as needed

### Converting Sync Tasks to Async

**Before (Sync)**:
```python
@celery_app.task
def sync_task():
    time.sleep(2)  # Blocks
    return {"done": True}
```

**After (Async with Gevent)**:
```python
async def async_task_helper():
    await asyncio.sleep(2)  # Non-blocking
    return {"done": True}

@celery_app.task
def sync_task():
    return run_async(async_task_helper())
```

## Troubleshooting

### Worker Not Starting

**Issue**: `No module named 'gevent'`

**Solution**: Install gevent
```bash
poetry install
```

### Tasks Hang

**Issue**: Task appears stuck

**Solution**: Check for blocking operations
- Replace `time.sleep()` with `await asyncio.sleep()`
- Replace `requests` with `httpx.AsyncClient`
- Use async database drivers

### High Memory Usage

**Issue**: Worker memory grows over time

**Solution**: Reduce `worker_max_tasks_per_child`
```python
worker_max_tasks_per_child=500  # More frequent restarts
```

### Tasks Fail with Event Loop Errors

**Issue**: `RuntimeError: This event loop is already running`

**Solution**: Ensure using `run_async` wrapper correctly
```python
# ❌ Wrong - nested event loop
async def task():
    result = await some_async()  # If called from async context
    return result

# ✅ Correct - proper wrapper
def celery_task():
    return run_async(some_async())
```

## Future: SQS Migration

For production scalability, migrate from Redis to AWS SQS:

1. Update broker URL in settings:
```python
CELERY_BROKER_URL = "sqs://"
```

2. Configure SQS transport options:
```python
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "region": "us-east-1",
    "queue_name_prefix": "celery-",
}
```

3. Install dependencies:
```bash
poetry add celery[sqs] boto3
```

4. Restart worker - no code changes needed!

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Gevent Documentation](http://www.gevent.org/)
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#tips-and-best-practices)

information
