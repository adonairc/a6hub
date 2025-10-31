#!/usr/bin/env python3
"""
Database migration script to add popularity metrics to projects table

Adds the following columns to the projects table:
- stars_count (INTEGER, default 0)
- views_count (INTEGER, default 0)

Usage:
    python scripts/migrate_add_popularity_metrics.py
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

def run_migration():
    """Add stars_count and views_count columns to projects table"""

    print("=" * 60)
    print("Migration: Add popularity metrics to projects table")
    print("=" * 60)
    print(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}")
    print()

    # Check if columns already exist using information_schema
    print("Checking if columns already exist...")

    with engine.connect() as conn:
        # Query information_schema to check for columns (this won't fail/abort transaction)
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'projects'
            AND column_name IN ('stars_count', 'views_count')
        """)

        result = conn.execute(check_query)
        existing_columns = [row[0] for row in result]

        if 'stars_count' in existing_columns and 'views_count' in existing_columns:
            print("✓ Columns already exist! No migration needed.")
            return True

        if existing_columns:
            print(f"⚠ Warning: Found existing columns: {existing_columns}")
            print("✗ Partial migration detected. Please check database state.")
            return False

        print("✗ Columns not found. Proceeding with migration...")

    # Run migration in a new connection with proper transaction handling
    with engine.begin() as conn:
        try:
            print("\n1. Adding stars_count column...")
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN stars_count INTEGER NOT NULL DEFAULT 0
            """))
            print("✓ stars_count column added successfully")

            print("\n2. Adding views_count column...")
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0
            """))
            print("✓ views_count column added successfully")

            print("\n" + "=" * 60)
            print("Migration completed successfully!")
            print("=" * 60)
            print("\nNew columns added:")
            print("  - stars_count (INTEGER, DEFAULT 0)")
            print("  - views_count (INTEGER, DEFAULT 0)")
            print("\nAll existing projects have been initialized with 0 for both fields.")

            return True

        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            print("\nTransaction will be rolled back automatically...")
            raise

if __name__ == "__main__":
    print()
    try:
        success = run_migration()
        print()

        if success:
            sys.exit(0)
        else:
            print("Migration failed. Please check the error messages above.")
            sys.exit(1)
    except Exception as e:
        print()
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
