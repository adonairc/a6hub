# a6hub Backend

Multi-tenant SaaS platform for collaborative chip design automation.

## Features

- 🔐 **JWT Authentication** - Secure user registration and login
- 📁 **Project Management** - Create and manage HDL projects with Git integration
- 📝 **File Management** - Upload, edit, and organize Verilog files
- ⚙️ **Job Queue** - Asynchronous simulation and build execution with Celery
- 🗄️ **Object Storage** - MinIO for scalable artifact storage
- 🎯 **RESTful API** - Clean, well-documented API endpoints

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Redis** - Message broker and caching
- **Celery** - Distributed task queue
- **MinIO** - S3-compatible object storage
- **Docker** - Containerization

## Project Structure

```
a6hub-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── projects.py     # Project CRUD
│   │       ├── files.py        # File management
│   │       ├── jobs.py         # Job management
│   │       └── router.py       # Main router
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── security.py         # JWT & password hashing
│   ├── db/
│   │   ├── base.py             # SQLAlchemy base
│   │   └── session.py          # Database session
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── project.py          # Project model
│   │   ├── project_file.py     # File model
│   │   └── job.py              # Job model
│   ├── schemas/
│   │   ├── user.py             # User schemas
│   │   ├── project.py          # Project schemas
│   │   └── job.py              # Job schemas
│   └── workers/
│       ├── celery_app.py       # Celery configuration
│       └── tasks.py            # Celery tasks
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Multi-container setup
└── .env.example                # Environment variables template
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd a6hub-backend

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

## Local Development

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL, Redis, and MinIO (via Docker or locally)
docker-compose up -d postgres redis minio

# Run the application
uvicorn main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Database Migrations

```bash
# Create a migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### LibreLane Worker Setup

The a6hub backend uses LibreLane from the [adonairc/librelane](https://github.com/adonairc/librelane) repository for ASIC design flows.

#### Installation

LibreLane is automatically installed from the GitHub repository when you install the backend dependencies:

```bash
# LibreLane is included in requirements.txt
pip install -r requirements.txt
```

This installs LibreLane directly from: `git+https://github.com/adonairc/librelane.git@main`

#### PDK Setup

LibreLane requires Process Design Kits (PDKs) to be installed. Configure the PDK root path in your environment:

```bash
# In .env file
PDK_ROOT=/path/to/pdk  # e.g., /opt/pdk or $HOME/.ciel
```

For open-source PDKs like SkyWater SKY130:

```bash
# Install using Volare (LibreLane's PDK manager)
pip install volare
volare enable --pdk sky130 sky130A
```

#### Running Builds

By default, builds run using the **locally installed LibreLane package** (not Docker). This provides:
- Faster execution (no Docker overhead)
- Better integration with the WebSocket progress streaming
- Direct access to the adonairc/librelane improvements

To use Docker mode instead, set `use_docker: true` in the build configuration.

#### Docker Mode (Optional)

If you prefer to run LibreLane in Docker:

```bash
# Build the Docker image from adonairc/librelane
git clone https://github.com/adonairc/librelane.git
cd librelane
docker build -t ghcr.io/adonairc/librelane:latest .

# Or pull if available
docker pull ghcr.io/adonairc/librelane:latest
```

Then configure builds with `use_docker: true` and `docker_image: "ghcr.io/adonairc/librelane:latest"`.

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Projects

- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List user's projects
- `GET /api/v1/projects/public` - List public projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Files

- `GET /api/v1/projects/{id}/files` - List project files
- `POST /api/v1/projects/{id}/files` - Create file
- `GET /api/v1/projects/{id}/files/{file_id}` - Get file content
- `PUT /api/v1/projects/{id}/files/{file_id}` - Update file
- `DELETE /api/v1/projects/{id}/files/{file_id}` - Delete file

### Jobs

- `POST /api/v1/projects/{id}/jobs` - Create job
- `GET /api/v1/projects/{id}/jobs` - List project jobs
- `GET /api/v1/projects/{id}/jobs/{job_id}` - Get job details
- `GET /api/v1/projects/{id}/jobs/{job_id}/logs` - Get job logs
- `DELETE /api/v1/projects/{id}/jobs/{job_id}` - Cancel job

## Configuration

Key environment variables:

```bash
# Application
PROJECT_NAME=a6hub
SECRET_KEY=<generate-secure-key>

# Database
POSTGRES_HOST=localhost
POSTGRES_USER=a6hub
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=a6hub

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=<secure-password>
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Deployment

### Production Considerations

1. **Security**
   - Use strong `SECRET_KEY`
   - Enable HTTPS
   - Configure CORS properly
   - Use secure passwords for databases

2. **Scaling**
   - Run multiple Celery workers
   - Use connection pooling
   - Enable Redis persistence
   - Configure load balancer

3. **Monitoring**
   - Set up logging aggregation
   - Monitor Celery queue lengths
   - Track database performance
   - Alert on job failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: http://localhost:8000/docs
