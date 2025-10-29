# a6hub Backend Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                          │
│                    http://localhost:3000                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP/REST API + WebSocket
                               │ (JWT Authentication)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)                      │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │    Auth     │  │   Projects   │  │     Jobs     │             │
│  │  Endpoints  │  │   Endpoints  │  │  Endpoints   │             │
│  └─────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Files     │  │   Security   │  │    Core      │             │
│  │  Endpoints  │  │   (JWT)      │  │   Config     │             │
│  └─────────────┘  └──────────────┘  └──────────────┘             │
└──────────────┬───────────────────────────────────┬─────────────────┘
               │                                   │
               │ SQLAlchemy ORM                    │ Celery Tasks
               │                                   │
      ┌────────▼───────────┐              ┌────────▼──────────┐
      │   PostgreSQL       │              │  Redis Broker     │
      │   (Port 5432)      │              │   (Port 6379)     │
      │                    │              │                   │
      │  ┌──────────────┐  │              └────────┬──────────┘
      │  │    users     │  │                       │
      │  ├──────────────┤  │                       │
      │  │   projects   │  │              ┌────────▼──────────┐
      │  ├──────────────┤  │              │  Celery Workers   │
      │  │ project_files│  │              │                   │
      │  ├──────────────┤  │              │  ┌─────────────┐  │
      │  │     jobs     │  │              │  │ Simulation  │  │
      │  └──────────────┘  │              │  │   Tasks     │  │
      └────────────────────┘              │  ├─────────────┤  │
                                          │  │   Build     │  │
                                          │  │   Tasks     │  │
                                          │  └─────────────┘  │
                                          └──────┬────────────┘
                                                 │
                                                 │ Store Artifacts
                                                 │
                                          ┌──────▼────────────┐
                                          │   MinIO Storage   │
                                          │  (Port 9000/9001) │
                                          │                   │
                                          │  ┌─────────────┐  │
                                          │  │   GDSII     │  │
                                          │  │   Files     │  │
                                          │  ├─────────────┤  │
                                          │  │  Build      │  │
                                          │  │  Logs       │  │
                                          │  ├─────────────┤  │
                                          │  │ Simulation  │  │
                                          │  │  Outputs    │  │
                                          │  └─────────────┘  │
                                          └───────────────────┘
```

## Request Flow

### 1. User Registration/Login Flow
```
User → POST /api/v1/auth/register → FastAPI
                                    ├─> Hash password (bcrypt)
                                    ├─> Save to PostgreSQL
                                    └─> Return user data

User → POST /api/v1/auth/login → FastAPI
                                 ├─> Verify password
                                 ├─> Generate JWT token
                                 └─> Return token
```

### 2. Project Creation Flow
```
User → POST /api/v1/projects → FastAPI
      (with JWT token)         ├─> Verify token
                               ├─> Create project in PostgreSQL
                               ├─> Initialize Git repository (optional)
                               └─> Return project data
```

### 3. File Upload Flow
```
User → POST /api/v1/projects/{id}/files → FastAPI
      (with HDL content)                  ├─> Verify ownership
                                          ├─> Validate file size
                                          ├─> Save to PostgreSQL
                                          └─> Return file metadata
```

### 4. Job Execution Flow
```
User → POST /api/v1/projects/{id}/jobs → FastAPI
      (simulation/build request)         ├─> Create job in PostgreSQL
                                         ├─> Queue task in Redis
                                         └─> Return job ID

                                         ┌─────────────────────┐
                                         │  Celery Worker      │
                                         ├─────────────────────┤
                                         │ 1. Pick up task     │
                                         │ 2. Update status    │
                                         │ 3. Create work dir  │
                                         │ 4. Run EDA tools    │
                                         │ 5. Capture logs     │
                                         │ 6. Upload artifacts │
                                         │ 7. Update job       │
                                         └─────────────────────┘

User → GET /api/v1/projects/{id}/jobs/{job_id} → FastAPI
                                                  └─> Return status/logs
```

## Component Details

### FastAPI Backend
- **Technology**: Python 3.11, FastAPI, Uvicorn
- **Port**: 8000
- **Responsibilities**:
  - API endpoints
  - Request validation (Pydantic)
  - Authentication (JWT)
  - Database operations (SQLAlchemy)
  - Task queuing (Celery)
  - CORS handling

### PostgreSQL Database
- **Technology**: PostgreSQL 15
- **Port**: 5432
- **Responsibilities**:
  - User data storage
  - Project metadata
  - File content storage
  - Job tracking
  - Relationships and constraints

### Redis
- **Technology**: Redis 7
- **Port**: 6379
- **Responsibilities**:
  - Celery message broker
  - Task queue management
  - Result backend
  - Optional: caching layer

### Celery Workers
- **Technology**: Celery 5.3 with Python 3.11
- **Responsibilities**:
  - Execute simulation tasks (Verilator/Icarus)
  - Execute build tasks (LibreLane)
  - Log management
  - Artifact generation
  - Status updates

### MinIO Storage
- **Technology**: MinIO (S3-compatible)
- **Ports**: 9000 (API), 9001 (Console)
- **Responsibilities**:
  - GDSII file storage
  - Build artifact storage
  - Log file storage
  - Large file handling

## Data Flow

### Authentication Flow
```
┌──────┐     ┌─────────┐     ┌──────────┐     ┌──────────────┐
│Client├────>│ FastAPI ├────>│PostgreSQL├────>│ JWT Token    │
└──────┘     └─────────┘     └──────────┘     └──────┬───────┘
                                                      │
                                                      ▼
┌──────┐     ┌─────────┐                      ┌──────────────┐
│Client│<────┤ FastAPI │                      │ Stored in    │
└──────┘     └─────────┘                      │ Client       │
                                              └──────────────┘
```

### Job Processing Flow
```
┌──────┐     ┌─────────┐     ┌──────────┐     ┌──────┐
│Client├────>│ FastAPI ├────>│PostgreSQL│<────┤Worker│
└──────┘     └────┬────┘     └──────────┘     └───┬──┘
                  │                                 │
                  │          ┌─────────┐           │
                  └─────────>│  Redis  │<──────────┘
                             └─────────┘
                                                    │
                             ┌─────────┐           │
                             │  MinIO  │<──────────┘
                             └─────────┘
                          (Store Artifacts)
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Transport Layer                                     │
│     └─> HTTPS (TLS/SSL) - Production                   │
│                                                         │
│  2. Authentication Layer                                │
│     ├─> JWT Tokens (HS256)                             │
│     ├─> Token Expiration (7 days)                      │
│     └─> Bearer Token in Headers                        │
│                                                         │
│  3. Authorization Layer                                 │
│     ├─> User Ownership Checks                          │
│     ├─> Project Visibility (Public/Private)            │
│     └─> Role-based Access (Future)                     │
│                                                         │
│  4. Data Layer                                          │
│     ├─> Password Hashing (bcrypt)                      │
│     ├─> SQL Injection Prevention (SQLAlchemy)          │
│     └─> Input Validation (Pydantic)                    │
│                                                         │
│  5. Network Layer                                       │
│     ├─> CORS Configuration                             │
│     ├─> Rate Limiting (Future)                         │
│     └─> IP Whitelisting (Future)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Production Deployment                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐                                         │
│  │   Nginx    │  (Reverse Proxy, SSL, Static Files)     │
│  └──────┬─────┘                                         │
│         │                                                │
│  ┌──────▼─────────────────────────────────────────┐    │
│  │        FastAPI Instances (Load Balanced)       │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐           │    │
│  │  │Backend1│  │Backend2│  │Backend3│           │    │
│  │  └────────┘  └────────┘  └────────┘           │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Celery Workers (Horizontal Scaling)         │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐│  │
│  │  │Worker1 │  │Worker2 │  │Worker3 │  │Worker4 ││  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘│  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │   Redis  │  │    MinIO     │     │
│  │  (Primary +  │  │  Cluster │  │  Distributed │     │
│  │   Replicas)  │  │          │  │              │     │
│  └──────────────┘  └──────────┘  └──────────────┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Scalability Considerations

1. **Horizontal Scaling**
   - Multiple FastAPI instances behind load balancer
   - Multiple Celery workers for parallel job execution
   - Redis cluster for high availability
   - MinIO distributed mode

2. **Vertical Scaling**
   - Increase worker container resources
   - PostgreSQL connection pooling
   - Redis memory optimization

3. **Caching Strategy**
   - Redis for session caching
   - CDN for static assets (future)
   - Database query caching

4. **Performance Optimization**
   - Async endpoints where appropriate
   - Database indexes on frequently queried fields
   - Connection pooling
   - Task result expiration
