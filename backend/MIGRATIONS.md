# Database Migrations

This document describes how to run database migrations for the a6hub backend.

## Current Migrations

### 2025-01-XX: Add Popularity Metrics to Projects

**What it does:**
Adds `stars_count` and `views_count` columns to the `projects` table to track project popularity.

**How to run:**

1. Make sure your backend environment is set up and the database is accessible:
   ```bash
   cd backend
   ```

2. Run the migration script:
   ```bash
   python scripts/migrate_add_popularity_metrics.py
   ```

3. The script will:
   - Check if columns already exist (safe to run multiple times)
   - Add `stars_count` column (INTEGER, default 0)
   - Add `views_count` column (INTEGER, default 0)
   - Initialize all existing projects with 0 for both fields

**Expected output:**
```
============================================================
Migration: Add popularity metrics to projects table
============================================================
Database: localhost/a6hub

Checking if columns already exist...
✗ Columns not found. Proceeding with migration...

1. Adding stars_count column...
✓ stars_count column added successfully

2. Adding views_count column...
✓ views_count column added successfully

============================================================
Migration completed successfully!
============================================================

New columns added:
  - stars_count (INTEGER, DEFAULT 0)
  - views_count (INTEGER, DEFAULT 0)

All existing projects have been initialized with 0 for both fields.
```

**If columns already exist:**
```
Checking if columns already exist...
✓ Columns already exist! No migration needed.
```

## Running with Docker

If you're using Docker Compose:

```bash
# Run migration in the backend container
docker-compose exec backend python scripts/migrate_add_popularity_metrics.py
```

Or if the backend isn't running yet:

```bash
# Run a temporary container to execute migration
docker-compose run --rm backend python scripts/migrate_add_popularity_metrics.py
```

## Troubleshooting

### Error: "relation 'projects' does not exist"

The database tables haven't been created yet. Start the backend application first to create the base tables:

```bash
python main.py
# or
docker-compose up backend
```

Then run the migration.

### Error: "column 'stars_count' already exists"

The migration has already been run successfully. No action needed.

### Error: "permission denied"

Make sure the migration script is executable:

```bash
chmod +x scripts/migrate_add_popularity_metrics.py
```

## Manual Migration (if script fails)

If the migration script fails, you can run the SQL commands manually:

```sql
-- Connect to your database and run:
ALTER TABLE projects ADD COLUMN stars_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE projects ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0;
```

## Future Migrations

When creating new migrations:

1. Create a new Python script in `scripts/` following the naming pattern: `migrate_<description>.py`
2. Document it in this file
3. Make it idempotent (safe to run multiple times)
4. Include clear success/failure messages
5. Test on a development database first

## Alembic Setup (Future)

For better migration management, consider setting up Alembic:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini and env.py
# Generate migrations with: alembic revision --autogenerate -m "description"
# Run migrations with: alembic upgrade head
```

This would provide:
- Version control for database schema
- Automatic migration generation
- Rollback capabilities
- Migration history tracking
