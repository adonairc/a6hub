# Troubleshooting Guide

## MinIO Connection Issues

### Error: "Failed to establish a new connection: Connection refused"

**Full Error:**
```
urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=9000):
Max retries exceeded with url: /a6hub-files?location=
(Caused by NewConnectionError: Failed to establish a new connection: [Errno 111] Connection refused)
```

**Cause:**
The Celery worker cannot connect to MinIO because the endpoint is misconfigured.

**Solutions:**

#### Running with Docker Compose (Recommended)

If using `docker-compose up`, the services are already configured correctly:

```bash
# Start all services
cd backend
docker-compose up -d

# Check that all services are running
docker-compose ps

# Check logs if worker is failing
docker-compose logs celery-worker
```

The docker-compose.yml already sets `MINIO_ENDPOINT=minio:9000` for containers.

#### Running Worker Locally (Development)

If running the Celery worker locally (outside Docker), create a `.env` file:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and ensure MinIO settings point to localhost:

```bash
# MinIO (for local development)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_FILES_BUCKET=a6hub-files
MINIO_SECURE=false
```

Then ensure MinIO is running:

```bash
# Option 1: Run just MinIO with Docker
docker run -d \
  -p 9000:9000 -p 9001:9001 \
  --name a6hub-minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Option 2: Use docker-compose for all infrastructure
docker-compose up postgres redis minio -d
```

Start the worker locally:

```bash
celery -A app.workers.celery_app worker --loglevel=info --queues=build,simulation
```

#### Mixed Setup (Backend locally, Worker in Docker)

If running the FastAPI backend locally but worker in Docker:

1. Backend `.env` should use `localhost:9000`
2. Worker (in docker-compose) uses `minio:9000` (already configured)

Start services:

```bash
# Start infrastructure only
docker-compose up postgres redis minio celery-worker -d

# Run backend locally
cd backend
uvicorn main:app --reload
```

#### Checking MinIO Connectivity

Test MinIO is accessible:

```bash
# From host machine
curl http://localhost:9000/minio/health/live

# From inside Docker network
docker exec a6hub-celery-worker curl http://minio:9000/minio/health/live
```

Access MinIO Console (Web UI):

```
http://localhost:9001
Username: minioadmin
Password: minioadmin
```

### Other Common Issues

#### Port Already in Use

If port 9000 is already in use:

```bash
# Check what's using port 9000
lsof -i :9000

# Change MinIO port in docker-compose.yml
ports:
  - "9002:9000"  # Change host port to 9002

# Update MINIO_ENDPOINT accordingly
MINIO_ENDPOINT=localhost:9002
```

#### Bucket Not Found

If you see "bucket does not exist" errors:

```bash
# The application auto-creates buckets, but you can manually create them
# Access MinIO Console at http://localhost:9001
# Or use mc (MinIO Client)

mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/a6hub-files
mc mb local/a6hub-artifacts
```

#### Permission Denied

Ensure MinIO has correct access credentials:

```bash
# Check credentials match in:
# - docker-compose.yml (MINIO_ROOT_USER/PASSWORD)
# - .env (MINIO_ACCESS_KEY/SECRET_KEY)
```

## Database Connection Issues

### Error: "Connection refused" to PostgreSQL

**Solution:**

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# For local development, update .env:
POSTGRES_HOST=localhost  # or 'postgres' if in Docker
```

## Redis Connection Issues

### Error: "Error 111 connecting to localhost:6379"

**Solution:**

```bash
# Check Redis is running
docker-compose ps redis

# For local development:
REDIS_HOST=localhost  # or 'redis' if in Docker
```

## LibreLane Build Issues

### Error: "Docker command not found"

The Celery worker needs access to Docker to run LibreLane containers.

**Solution:**

Mount Docker socket in docker-compose.yml (already configured):

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Error: "Permission denied" accessing Docker socket

**Solution:**

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER

# Or run worker as root (not recommended for production)
docker-compose exec -u root celery-worker bash
```

## Getting Help

If issues persist:

1. Check logs:
   ```bash
   docker-compose logs -f celery-worker
   docker-compose logs -f backend
   ```

2. Check service health:
   ```bash
   docker-compose ps
   ```

3. Restart services:
   ```bash
   docker-compose restart celery-worker
   ```

4. Full reset (WARNING: deletes data):
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```
