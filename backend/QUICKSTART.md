# Quick Start Guide

Get a6hub running in 5 minutes with Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Port 8000, 3000, 5432, 6379, 9000, 9001, and 5555 available

## Quick Start

### 1. Start All Services

```bash
cd backend
docker-compose up -d
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ MinIO (ports 9000, 9001)
- ✅ FastAPI Backend (port 8000)
- ✅ Celery Worker (background)
- ✅ Flower Dashboard (port 5555)

### 2. Check Services Status

```bash
docker-compose ps
```

All services should show "Up" status with health checks passing.

### 3. Access the Application

**Backend API**: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Flower Dashboard**: http://localhost:5555
- Monitor Celery workers and tasks
- View queue status and statistics

**MinIO Console**: http://localhost:9001
- Login: minioadmin / minioadmin

### 4. Start Frontend (in another terminal)

```bash
cd ../frontend
npm install
npm run dev
```

**Frontend**: http://localhost:3000

### 5. Create Your First Project

1. Register an account at http://localhost:3000/auth/register
2. Login
3. Click "New Project"
4. Upload Verilog files
5. Go to "Build" tab
6. Select a preset (e.g., "Minimal Flow")
7. Click "Start Build"
8. Monitor progress in Flower: http://localhost:5555

## Verify Celery Integration

Test that Celery workers are running and connected to Redis:

```bash
cd backend
python scripts/test-celery.py
```

Expected output:
```
Testing Celery connection to Redis...
✓ Successfully connected to Redis broker

Testing worker availability...
✓ Found 1 active worker(s)

Testing queue configuration...
✓ Active queues:
  - build
  - simulation

✓ All tests passed!
```

## View Logs

**All services**:
```bash
docker-compose logs -f
```

**Specific service**:
```bash
docker-compose logs -f celery-worker
docker-compose logs -f backend
docker-compose logs -f redis
```

**Worker logs** (shows build progress):
```bash
docker-compose logs -f celery-worker | grep "LibreLane"
```

## Stop Services

```bash
docker-compose down
```

**To also remove volumes** (deletes all data):
```bash
docker-compose down -v
```

## Restart Services

```bash
docker-compose restart
```

**Restart specific service**:
```bash
docker-compose restart celery-worker
docker-compose restart backend
```

## Troubleshooting

### Services won't start

Check if ports are available:
```bash
# Check if ports are in use
netstat -an | grep -E '(8000|6379|5432|9000|5555)'
```

Stop conflicting services or change ports in docker-compose.yml.

### Worker not processing jobs

1. Check worker is running:
   ```bash
   docker-compose ps celery-worker
   ```

2. Check worker logs:
   ```bash
   docker-compose logs celery-worker
   ```

3. Verify Redis connection:
   ```bash
   docker-compose exec redis redis-cli ping
   ```

4. Restart worker:
   ```bash
   docker-compose restart celery-worker
   ```

### Build fails with Docker permission error

The worker needs access to Docker socket. Verify mount in docker-compose.yml:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Database connection error

Wait for PostgreSQL to fully start:
```bash
docker-compose logs postgres
```

Look for: `database system is ready to accept connections`

## Development Mode

For active development:

### Backend only (with hot reload):
```bash
cd backend
docker-compose up postgres redis minio  # Start dependencies only

# In another terminal
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal
./scripts/start-worker.sh  # Start worker locally

# In another terminal (optional)
./scripts/start-flower.sh  # Start monitoring
```

### Frontend:
```bash
cd frontend
npm run dev  # Hot reload enabled
```

## Production Deployment

For production, see:
- [REDIS_CELERY_SETUP.md](REDIS_CELERY_SETUP.md) - Full Redis/Celery configuration
- [LIBRELANE_INTEGRATION.md](../LIBRELANE_INTEGRATION.md) - LibreLane flow details

Production checklist:
- [ ] Set strong passwords for PostgreSQL
- [ ] Enable Redis authentication
- [ ] Use environment variables for secrets
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL/TLS certificates
- [ ] Configure backups for PostgreSQL
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Scale workers: `docker-compose up -d --scale celery-worker=3`

## Next Steps

- Read [REDIS_CELERY_SETUP.md](REDIS_CELERY_SETUP.md) for detailed worker configuration
- Read [LIBRELANE_INTEGRATION.md](../LIBRELANE_INTEGRATION.md) for build flow options
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Browse API docs at http://localhost:8000/docs

## URLs Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | User registration |
| Backend API | http://localhost:8000 | Token-based auth |
| API Docs | http://localhost:8000/docs | - |
| Flower | http://localhost:5555 | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Run tests: `python scripts/test-celery.py`
- Check service health: `docker-compose ps`
- Review documentation in `/backend` directory

Happy building! 🚀
