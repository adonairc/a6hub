# a6hub Backend - Quick Reference Guide

## 🎯 Project Overview

The a6hub backend is a FastAPI-based REST API for a multi-tenant SaaS platform that enables collaborative chip design automation. It handles user authentication, project management, file storage, and asynchronous job execution for HDL simulation and ASIC builds.

## 📁 Key Components

### 1. **Authentication System** (`app/api/v1/auth.py`)
- JWT-based authentication
- User registration and login
- Password hashing with bcrypt
- Token expiration: 7 days (configurable)

### 2. **Project Management** (`app/api/v1/projects.py`)
- CRUD operations for chip design projects
- Public/private visibility control
- Slug-based project URLs
- Git integration ready

### 3. **File Management** (`app/api/v1/files.py`)
- Upload/download HDL files
- In-database storage for text files
- File size limits (configurable)
- Support for Verilog/SystemVerilog

### 4. **Job Queue** (`app/workers/`)
- Celery-based task execution
- Redis as message broker
- Support for simulation and build jobs
- Real-time log streaming

### 5. **Database Models** (`app/models/`)
- **User**: Authentication and ownership
- **Project**: Container for designs
- **ProjectFile**: HDL and configuration files
- **Job**: Asynchronous task tracking

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Option 2: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start services
uvicorn main:app --reload

# In separate terminal, start worker
celery -A app.workers.celery_app worker --loglevel=info
```

## 🔑 Environment Variables

Critical variables to configure:

```bash
SECRET_KEY=<generate-with-openssl-rand-hex-32>
POSTGRES_PASSWORD=<secure-database-password>
MINIO_SECRET_KEY=<secure-storage-password>
```

## 📊 Database Schema

```
users
├── id (PK)
├── email (unique)
├── username (unique)
├── hashed_password
└── timestamps

projects
├── id (PK)
├── name
├── slug (unique)
├── visibility (public/private)
├── owner_id (FK → users)
└── timestamps

project_files
├── id (PK)
├── filename
├── filepath
├── content
├── project_id (FK → projects)
└── timestamps

jobs
├── id (PK)
├── job_type (simulation/build)
├── status (pending/running/completed/failed)
├── celery_task_id
├── logs
├── project_id (FK → projects)
├── user_id (FK → users)
└── timestamps
```

## 🔌 API Endpoints

### Authentication
```
POST   /api/v1/auth/register    # Register new user
POST   /api/v1/auth/login       # Get access token
GET    /api/v1/auth/me          # Get current user
```

### Projects
```
POST   /api/v1/projects              # Create project
GET    /api/v1/projects              # List user's projects
GET    /api/v1/projects/public       # List public projects
GET    /api/v1/projects/{id}         # Get project
PUT    /api/v1/projects/{id}         # Update project
DELETE /api/v1/projects/{id}         # Delete project
```

### Files
```
GET    /api/v1/projects/{id}/files           # List files
POST   /api/v1/projects/{id}/files           # Upload file
GET    /api/v1/projects/{id}/files/{file_id} # Get file
PUT    /api/v1/projects/{id}/files/{file_id} # Update file
DELETE /api/v1/projects/{id}/files/{file_id} # Delete file
```

### Jobs
```
POST   /api/v1/projects/{id}/jobs            # Create job
GET    /api/v1/projects/{id}/jobs            # List jobs
GET    /api/v1/projects/{id}/jobs/{job_id}   # Get job details
GET    /api/v1/projects/{id}/jobs/{job_id}/logs  # Get logs
DELETE /api/v1/projects/{id}/jobs/{job_id}   # Cancel job
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# With coverage
pytest --cov=app tests/
```

## 🔧 Common Tasks

### Add a New Endpoint
1. Create route function in `app/api/v1/<module>.py`
2. Add request/response schemas in `app/schemas/`
3. Include router in `app/api/v1/router.py`

### Add a New Database Model
1. Create model in `app/models/<model>.py`
2. Add schema in `app/schemas/<model>.py`
3. Run database migration (if using Alembic)

### Add a New Celery Task
1. Define task in `app/workers/tasks.py`
2. Configure task routing in `app/workers/celery_app.py`
3. Call task from API endpoint using `.delay()`

## 🐛 Debugging

### Check Database Connection
```bash
docker exec -it a6hub-postgres psql -U a6hub -d a6hub
```

### Check Redis
```bash
docker exec -it a6hub-redis redis-cli
> PING
> KEYS *
```

### View Celery Tasks
```bash
# In Python shell
from app.workers.celery_app import celery_app
i = celery_app.control.inspect()
i.active()
i.scheduled()
```

### Common Issues

**Database connection error**
- Ensure PostgreSQL is running: `docker-compose ps`
- Check credentials in `.env`

**Celery tasks not executing**
- Verify Redis is running
- Check worker logs: `docker-compose logs celery-worker`

**Import errors**
- Ensure all `__init__.py` files exist
- Check Python path includes project root

## 📦 Dependencies

**Core**
- FastAPI 0.104.1 - Web framework
- SQLAlchemy 2.0.23 - ORM
- Pydantic 2.x - Data validation
- Uvicorn 0.24.0 - ASGI server

**Database**
- PostgreSQL 15 - Primary database
- psycopg2-binary 2.9.9 - PostgreSQL adapter

**Task Queue**
- Celery 5.3.4 - Distributed task queue
- Redis 5.0.1 - Message broker

**Security**
- python-jose 3.3.0 - JWT handling
- passlib 1.7.4 - Password hashing

**Storage**
- MinIO 7.2.0 - Object storage client

## 🚀 Next Steps

### MVP Completion
- [ ] Integrate WebSocket for real-time logs
- [ ] Implement MinIO file uploads
- [ ] Add LibreLane container integration
- [ ] Set up PDK mounts
- [ ] Add Git repository cloning

### Post-MVP
- [ ] OAuth integration (GitHub, Google)
- [ ] Organization accounts
- [ ] Project forking
- [ ] GDSII viewer integration
- [ ] Rate limiting
- [ ] Admin dashboard

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [API Documentation](http://localhost:8000/docs) (when running)

## 💡 Tips

1. **Use the OpenAPI docs**: Visit `/docs` for interactive API testing
2. **Check logs regularly**: `docker-compose logs -f`
3. **Keep .env secure**: Never commit `.env` to version control
4. **Test locally first**: Use SQLite for quick local testing
5. **Monitor resources**: Watch Docker container resource usage

---

**Need Help?** Check README.md for detailed setup instructions or open an issue.
