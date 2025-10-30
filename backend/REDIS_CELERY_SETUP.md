# Redis and Celery Integration Guide

This document describes the Redis and Celery integration for a6hub's asynchronous job processing system.

## Overview

The a6hub platform uses **Redis** as a message broker and **Celery** as a distributed task queue to handle long-running ASIC build and simulation jobs asynchronously.

### Architecture

```
┌─────────────┐
│   FastAPI   │  Creates jobs
│   Backend   │  ──────┐
└─────────────┘        │
                       ▼
                ┌─────────────┐
                │    Redis    │  Message broker
                │   (Queue)   │  & Result backend
                └─────────────┘
                       │
                       ▼
                ┌─────────────┐
                │   Celery    │  Processes jobs
                │   Workers   │  (with Docker access)
                └─────────────┘
                       │
                       ▼
                ┌─────────────┐
                │  LibreLane  │  ASIC builds
                │   Docker    │  in containers
                └─────────────┘
```

## Components

### 1. Redis (Message Broker + Result Backend)

**Purpose**:
- Stores job queue (tasks waiting to be executed)
- Stores job results and status
- Enables communication between FastAPI backend and Celery workers

**Configuration**:
- Port: `6379` (default)
- Database: `0` (default)
- Image: `redis:7-alpine`

**Health Check**:
```bash
redis-cli ping
# Expected output: PONG
```

### 2. Celery Workers

**Purpose**:
- Execute asynchronous build and simulation jobs
- Run LibreLane in Docker containers
- Update job status in database

**Configuration**:
- Queues: `build`, `simulation`
- Concurrency: `2` (processes 2 jobs simultaneously)
- Max tasks per child: `50` (worker restarts after 50 jobs)

**Task Routing**:
- `run_build` → `build` queue
- `run_simulation` → `simulation` queue

### 3. Flower (Monitoring Dashboard)

**Purpose**:
- Real-time monitoring of Celery workers
- View active/pending/completed tasks
- Worker statistics and health

**Access**: http://localhost:5555

## Docker Compose Setup

### Services

#### Redis
```yaml
redis:
  image: redis:7-alpine
  ports: ["6379:6379"]
  volumes: [redis_data:/data]
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

#### Celery Worker
```yaml
celery-worker:
  build:
    dockerfile: Dockerfile.worker  # Includes Docker CLI
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Docker access
    - storage_data:/tmp/a6hub-storage
  environment:
    - REDIS_HOST=redis
    - CELERY_BROKER_URL=redis://redis:6379/0
  command: celery -A app.workers.celery_app worker --loglevel=info --queues=build,simulation --concurrency=2
```

#### Flower
```yaml
flower:
  ports: ["5555:5555"]
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  command: celery -A app.workers.celery_app flower --port=5555
```

## Configuration

### Environment Variables

**Backend and Worker**:
```bash
REDIS_HOST=localhost          # or 'redis' in Docker
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Celery Configuration (`app/workers/celery_app.py`)

Key settings:
```python
# Task acknowledgment - only after completion
task_acks_late=True

# Don't prefetch tasks (important for long-running jobs)
worker_prefetch_multiplier=1

# Task time limits (1 hour default)
task_time_limit=3600
task_soft_time_limit=3540

# Result expiration (24 hours)
result_expires=86400

# Connection retry on startup
broker_connection_retry_on_startup=True
```

## Usage

### Starting the Stack

**With Docker Compose** (recommended):
```bash
cd backend
docker-compose up -d
```

This starts:
- PostgreSQL (database)
- Redis (message broker)
- MinIO (storage)
- FastAPI backend
- Celery worker
- Flower dashboard

**Check status**:
```bash
docker-compose ps
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f redis
```

### Local Development

If running backend locally (outside Docker):

**1. Start Redis**:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**2. Start Celery Worker**:
```bash
cd backend
./scripts/start-worker.sh
```

**3. Start Flower (optional)**:
```bash
./scripts/start-flower.sh
```

**4. Start Backend**:
```bash
uvicorn main:app --reload
```

### Testing Integration

Run the test script to verify everything is working:

```bash
cd backend
python scripts/test-celery.py
```

Expected output:
```
============================================================
Celery + Redis Integration Test
============================================================

Testing Celery connection to Redis...
✓ Successfully connected to Redis broker

Testing worker availability...
✓ Found 1 active worker(s):
  - celery@hostname
    Pool: prefork
    Max concurrency: 2

Testing queue configuration...
✓ Active queues:
  Worker: celery@hostname
    - build (routing_key: build.run)
    - simulation (routing_key: simulation.run)

Registered tasks:
  Worker: celery@hostname
    - app.workers.tasks.run_build
    - app.workers.tasks.run_simulation

============================================================
Test Summary
============================================================
Connection           ✓ PASS
Workers              ✓ PASS
Queues               ✓ PASS
Tasks                ✓ PASS

Passed: 4/4

✓ All tests passed! Celery is properly configured.
```

## Job Flow

### 1. Job Creation (FastAPI)

User creates a build job via API:
```python
# In builds.py endpoint
job = Job(
    job_type=JobType.BUILD,
    status=JobStatus.PENDING,
    config=config_dict,
    project_id=project_id,
    user_id=current_user.id
)
db.add(job)
db.commit()

# Queue Celery task
task = run_build.delay(job.id)
job.celery_task_id = task.id
db.commit()
```

### 2. Task Queuing (Redis)

Task is serialized and sent to Redis:
```json
{
  "task": "app.workers.tasks.run_build",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "args": [123],
  "kwargs": {},
  "queue": "build"
}
```

### 3. Task Execution (Celery Worker)

Worker picks up task and executes:
```python
# Worker logs
[INFO] Task app.workers.tasks.run_build[550e8400...] received
[INFO] Task app.workers.tasks.run_build[550e8400...] starting
[INFO] Starting LibreLane build job 123
[INFO] Task app.workers.tasks.run_build[550e8400...] succeeded
```

### 4. Result Storage (Redis)

Task result is stored in Redis:
```json
{
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "job_id": 123,
    "artifacts_path": "jobs/123/artifacts"
  }
}
```

### 5. Status Polling (FastAPI)

User polls job status:
```python
GET /api/v1/builds/{project_id}/build/status
```

Response:
```json
{
  "job_id": 123,
  "status": "completed",
  "current_step": "Build Complete",
  "logs": "..."
}
```

## Monitoring

### Flower Dashboard

Access at http://localhost:5555

**Features**:
- Real-time task monitoring
- Worker statistics
- Task history
- Broker monitoring
- Configuration inspection

**Key Views**:
1. **Dashboard**: Overview of workers and tasks
2. **Workers**: Worker pool status and configuration
3. **Tasks**: All tasks (active, scheduled, completed, failed)
4. **Monitor**: Real-time task stream

### Redis CLI

Check queue status:
```bash
# Connect to Redis
redis-cli

# Check queue lengths
LLEN celery        # Default queue
LLEN build         # Build queue
LLEN simulation    # Simulation queue

# View queued tasks
LRANGE build 0 -1

# Check worker heartbeat
KEYS celery@*

# View task results
KEYS celery-task-meta-*
```

### Logs

**Worker logs** (shows task execution):
```bash
docker-compose logs -f celery-worker
```

**Backend logs** (shows task queuing):
```bash
docker-compose logs -f backend
```

## Troubleshooting

### Worker Not Starting

**Symptom**: Worker container exits immediately

**Solutions**:
1. Check Redis is running: `docker-compose ps redis`
2. Check Redis health: `redis-cli ping`
3. View worker logs: `docker-compose logs celery-worker`
4. Verify environment variables in docker-compose.yml

### Tasks Not Processing

**Symptom**: Jobs stuck in PENDING status

**Solutions**:
1. Check if worker is running: `docker-compose ps celery-worker`
2. Check worker is consuming from correct queue: `./scripts/test-celery.py`
3. Check Redis connection: `redis-cli ping`
4. Restart worker: `docker-compose restart celery-worker`

### Docker Socket Permission Denied

**Symptom**: Worker can't run LibreLane containers

**Error**: `permission denied while trying to connect to the Docker daemon socket`

**Solution**:
```bash
# Add worker user to docker group (if running locally)
sudo usermod -aG docker $USER

# Or ensure Docker socket is accessible
sudo chmod 666 /var/run/docker.sock
```

### Task Timeout

**Symptom**: Tasks killed after 1 hour

**Solution**:
Increase timeout in `core/config.py`:
```python
MAX_JOB_DURATION_SECONDS = 7200  # 2 hours
```

Then restart worker:
```bash
docker-compose restart celery-worker
```

### Redis Connection Refused

**Symptom**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solutions**:
1. If using Docker: Set `REDIS_HOST=redis` (not `localhost`)
2. If running locally: Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
3. Check Redis port: `netstat -an | grep 6379`

## Performance Tuning

### Worker Concurrency

Adjust based on CPU cores:
```bash
# In docker-compose.yml
command: celery -A app.workers.celery_app worker --concurrency=4
```

Or use autoscale:
```bash
command: celery -A app.workers.celery_app worker --autoscale=10,3
# Min: 3 workers, Max: 10 workers
```

### Redis Memory

Set max memory in docker-compose.yml:
```yaml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### Task Prefetching

For mixed workload (short + long tasks):
```python
# In celery_app.py
worker_prefetch_multiplier=4  # Prefetch up to 4 tasks per worker
```

For only long tasks (current setting):
```python
worker_prefetch_multiplier=1  # Don't prefetch
```

## Production Considerations

### High Availability

**Multiple Workers**:
```bash
docker-compose up -d --scale celery-worker=3
```

**Redis Sentinel** (for failover):
```yaml
redis-sentinel:
  image: redis:7-alpine
  command: redis-sentinel /etc/redis/sentinel.conf
```

### Security

**Redis Password**:
```yaml
redis:
  command: redis-server --requirepass yourpassword
```

Update connection:
```python
REDIS_URL = "redis://:yourpassword@redis:6379/0"
```

**Network Isolation**:
```yaml
networks:
  backend:
    internal: true
```

### Monitoring

**Production monitoring tools**:
- Prometheus + Grafana
- Sentry (for error tracking)
- ELK Stack (for log aggregation)

**Celery Events**:
```bash
celery -A app.workers.celery_app events
```

## References

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)

## Summary

✅ **Redis** serves as both message broker and result backend
✅ **Celery workers** process build/simulation jobs asynchronously
✅ **Flower** provides real-time monitoring dashboard
✅ **Docker socket** mounted for LibreLane container execution
✅ **Separate queues** for build and simulation jobs
✅ **Health checks** ensure service reliability
✅ **Scripts** provided for local development and testing

The integration is production-ready with proper error handling, retry logic, and monitoring capabilities.
