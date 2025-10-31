"""
Database migration to add progress tracking fields to jobs table

Adds:
- current_step: String field to track the current build step
- progress_data: JSON field to store structured progress information
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Add progress tracking fields to jobs table"""
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

    print("Starting migration: Add job progress tracking fields")

    # Check if columns already exist
    with engine.connect() as conn:
        check_current_step = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='jobs' AND column_name='current_step'
        """)

        check_progress_data = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='jobs' AND column_name='progress_data'
        """)

        has_current_step = conn.execute(check_current_step).fetchone() is not None
        has_progress_data = conn.execute(check_progress_data).fetchone() is not None

    # Perform migration in a transaction
    with engine.begin() as conn:
        if not has_current_step:
            print("Adding column: current_step")
            conn.execute(text("""
                ALTER TABLE jobs
                ADD COLUMN current_step VARCHAR
            """))
            print("✓ Added current_step column")
        else:
            print("✓ Column current_step already exists")

        if not has_progress_data:
            print("Adding column: progress_data")
            conn.execute(text("""
                ALTER TABLE jobs
                ADD COLUMN progress_data JSON
            """))
            print("✓ Added progress_data column")
        else:
            print("✓ Column progress_data already exists")

    print("\nMigration completed successfully!")
    print("The jobs table now supports progress tracking:")
    print("  - current_step: tracks the current build step name")
    print("  - progress_data: stores structured progress info (completed steps, percentages, etc.)")


if __name__ == "__main__":
    migrate()
