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

    with engine.connect() as conn:
        # Check if columns already exist
        print("Checking if columns already exist...")

        try:
            # Try to select the columns - if they exist, this will succeed
            result = conn.execute(text("SELECT stars_count, views_count FROM projects LIMIT 1"))
            print("✓ Columns already exist! No migration needed.")
            return True
        except Exception:
            # Columns don't exist, proceed with migration
            print("✗ Columns not found. Proceeding with migration...")

        try:
            print("\n1. Adding stars_count column...")
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN stars_count INTEGER NOT NULL DEFAULT 0
            """))
            conn.commit()
            print("✓ stars_count column added successfully")

            print("\n2. Adding views_count column...")
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0
            """))
            conn.commit()
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
            print("\nRolling back changes...")
            conn.rollback()
            return False

if __name__ == "__main__":
    print()
    success = run_migration()
    print()

    if success:
        sys.exit(0)
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
