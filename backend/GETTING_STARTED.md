# Getting Started with a6hub Backend

Welcome to a6hub! This guide will get you up and running in 5 minutes.

## 🎯 What You're Building

a6hub is a cloud platform for chip design that lets users:
- Design ASIC chips in their browser
- Run HDL simulations (Verilog/SystemVerilog)
- Execute full RTL-to-GDSII builds using open-source PDKs
- Collaborate and share designs

This backend provides the API and job execution system.

## 📋 Prerequisites

You need:
- **Docker Desktop** (with Docker Compose)
- **Git** (to clone the project)
- **Text Editor** (VS Code recommended)
- **Terminal** (bash/zsh/PowerShell)

Optional:
- Python 3.11+ (for local development without Docker)
- PostgreSQL client (for database inspection)

## ⚡ Quick Start (5 minutes)

### Step 1: Get the Code
```bash
# If you have the files, skip this step
# Otherwise clone from your repository
git clone <your-repo-url>
cd a6hub-backend
```

### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# The defaults work for development, but you can customize:
# nano .env  (or use your favorite editor)
```

### Step 3: Start Everything
```bash
# Use the provided startup script
./start.sh

# OR manually with docker-compose
docker-compose up -d
```

Wait about 30 seconds for services to start.

### Step 4: Verify It's Running
```bash
# Check service status
docker-compose ps

# Should show all services as "healthy" or "running"

# Test the API
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"a6hub-backend"}
```

### Step 5: Explore the API
Open your browser to:
- **http://localhost:8000/docs** - Interactive API documentation
- **http://localhost:9001** - MinIO console (login: minioadmin/minioadmin)

## 🎮 Try It Out

### Create Your First User

1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/auth/register`
3. Click "Try it out"
4. Enter this JSON:
```json
{
  "email": "designer@example.com",
  "username": "chipdesigner",
  "password": "secure123",
  "full_name": "Chip Designer"
}
```
5. Click "Execute"
6. You should get a 201 response with your user data!

### Login to Get a Token

1. Find `POST /api/v1/auth/login`
2. Click "Try it out"
3. Enter:
```json
{
  "email": "designer@example.com",
  "password": "secure123"
}
```
4. Click "Execute"
5. Copy the `access_token` from the response

### Create a Project

1. Find `POST /api/v1/projects`
2. Click "Try it out"
3. Click the "🔒 Authorize" button at the top
4. Paste your token in the format: `Bearer your_token_here`
5. Click "Authorize"
6. Now enter project data:
```json
{
  "name": "My First ASIC",
  "description": "A simple LED blinker",
  "visibility": "private"
}
```
7. Click "Execute"
8. You now have a project!

### Upload a File

1. Find `POST /api/v1/projects/{project_id}/files`
2. Enter your project ID from the previous step
3. Enter file data:
```json
{
  "filename": "blinker.v",
  "filepath": "src/blinker.v",
  "content": "module blinker(input clk, output reg led); always @(posedge clk) led <= ~led; endmodule",
  "mime_type": "text/plain"
}
```
4. Click "Execute"

Congratulations! You've created a user, project, and uploaded your first HDL file! 🎉

## 🔍 Understanding the Structure

```
a6hub-backend/
├── app/                    # Main application code
│   ├── api/v1/            # API endpoints
│   │   ├── auth.py        # Login, register
│   │   ├── projects.py    # Project CRUD
│   │   ├── files.py       # File management
│   │   └── jobs.py        # Job execution
│   ├── models/            # Database models
│   ├── schemas/           # Request/response schemas
│   ├── core/              # Config and security
│   └── workers/           # Celery tasks
├── tests/                 # Test suite
├── main.py               # Application entry point
├── docker-compose.yml    # Services orchestration
└── requirements.txt      # Python dependencies
```

## 🛠️ Development Workflow

### Making Changes

1. **Edit code** - Files are mounted in containers, so changes reflect immediately
2. **Test your changes** - The API reloads automatically (--reload flag)
3. **View logs**:
```bash
docker-compose logs -f backend
```

### Working with the Database

```bash
# Connect to PostgreSQL
docker exec -it a6hub-postgres psql -U a6hub -d a6hub

# Useful commands:
\dt          # List tables
\d users     # Describe users table
SELECT * FROM users;  # Query users
\q           # Quit
```

### Working with Redis

```bash
# Connect to Redis
docker exec -it a6hub-redis redis-cli

# Useful commands:
PING         # Test connection
KEYS *       # List all keys
INFO         # Server info
```

### Viewing Celery Tasks

```bash
# View worker logs
docker-compose logs -f celery-worker

# Check task status in Python:
docker exec -it a6hub-celery-worker python3 -c "
from app.workers.celery_app import celery_app
i = celery_app.control.inspect()
print('Active:', i.active())
print('Scheduled:', i.scheduled())
"
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py

# Run with coverage
docker-compose exec backend pytest --cov=app tests/
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO

# Stop all containers and restart
docker-compose down
docker-compose up -d
```

### Database Connection Errors

```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Can't Authenticate

```bash
# Check if SECRET_KEY changed in .env
# If it did, existing tokens are invalid - create a new user

# Verify token format: should be "Bearer <token>"
# Common mistake: forgetting "Bearer " prefix
```

### Import Errors

```bash
# Restart backend service
docker-compose restart backend

# Check for syntax errors
docker-compose logs backend
```

## 📚 Next Steps

### Learn the API
- Read through each endpoint in `/docs`
- Try creating a complete workflow: user → project → file → job
- Experiment with different project visibility settings

### Add a Feature
Try adding a simple feature:
1. Add an endpoint to get user statistics
2. Create the route in `app/api/v1/auth.py`
3. Test it via `/docs`

Example:
```python
@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project_count = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).count()
    
    return {
        "username": current_user.username,
        "project_count": project_count
    }
```

### Explore the Code
- Start with `main.py` - see how the app initializes
- Look at `app/models/` - understand the data structure
- Read `app/api/v1/auth.py` - see how authentication works
- Check `app/workers/tasks.py` - see how jobs execute

### Read the Documentation
- `README.md` - Full setup guide
- `ARCHITECTURE.md` - System design
- `QUICK_REFERENCE.md` - API reference

## 🎓 Learning Resources

### FastAPI
- [Official Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Security](https://fastapi.tiangolo.com/tutorial/security/)

### SQLAlchemy
- [ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Relationships](https://docs.sqlalchemy.org/en/20/orm/relationships.html)

### Celery
- [First Steps](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html)
- [Task Basics](https://docs.celeryproject.org/en/stable/userguide/tasks.html)

### Docker
- [Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

## 💡 Tips for Success

1. **Use the Interactive Docs** - The `/docs` endpoint is your best friend
2. **Check Logs Often** - `docker-compose logs -f` shows what's happening
3. **Test Incrementally** - Make small changes and test each one
4. **Keep Services Running** - Use `docker-compose up -d` for background mode
5. **Read Error Messages** - FastAPI gives helpful error messages

## 🎯 Common Tasks

### Reset Everything
```bash
docker-compose down -v  # Remove volumes (deletes data!)
docker-compose up -d
```

### View All Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Update Dependencies
```bash
# Edit requirements.txt
docker-compose build backend
docker-compose up -d
```

### Database Backup
```bash
docker exec a6hub-postgres pg_dump -U a6hub a6hub > backup.sql
```

### Database Restore
```bash
cat backup.sql | docker exec -i a6hub-postgres psql -U a6hub -d a6hub
```

## 🤝 Getting Help

- **Check the Docs**: Read README.md and ARCHITECTURE.md
- **Search Issues**: Look for similar problems
- **Ask Questions**: Create an issue with details
- **Review PRD**: See PRD.md for project requirements

## ✅ Daily Development Checklist

- [ ] Services running: `docker-compose ps`
- [ ] API accessible: `curl http://localhost:8000/health`
- [ ] Can create user and login
- [ ] Database has tables: `\dt` in psql
- [ ] Worker is running: Check Celery logs
- [ ] Tests pass: `pytest`

## 🚀 You're Ready!

You now have a fully functional backend for chip design automation. Start exploring, experimenting, and building!

For more details, see:
- `README.md` - Complete documentation
- `QUICK_REFERENCE.md` - API reference
- `ARCHITECTURE.md` - System design

Happy coding! 🎉
