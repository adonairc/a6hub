"""
Database migration to add Modules table and MinIO support to project_files

This migration:
1. Creates the modules table for storing extracted design modules
2. Adds MinIO storage fields to project_files table
3. Adds module-related indexes for performance
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Add modules table and MinIO support"""
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

    print("Starting migration: Add modules table and MinIO support")
    print("=" * 60)

    # Check if modules table exists
    with engine.connect() as conn:
        check_modules_table = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='modules'
        """)

        modules_exists = conn.execute(check_modules_table).fetchone() is not None

        # Check if old 'metadata' column exists (needs rename)
        if modules_exists:
            check_old_column = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='modules' AND column_name='metadata'
            """)
            old_column_exists = conn.execute(check_old_column).fetchone() is not None
        else:
            old_column_exists = False

    # Perform migration in a transaction
    with engine.begin() as conn:
        if not modules_exists:
            print("\n1. Creating modules table...")
            conn.execute(text("""
                CREATE TABLE modules (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    module_type VARCHAR NOT NULL,
                    module_metadata JSON,
                    start_line INTEGER,
                    end_line INTEGER,
                    description TEXT,
                    file_id INTEGER NOT NULL REFERENCES project_files(id) ON DELETE CASCADE,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                )
            """))
            print("   ✓ Created modules table")

            # Create indexes
            print("\n2. Creating indexes on modules table...")
            conn.execute(text("CREATE INDEX ix_modules_name ON modules(name)"))
            conn.execute(text("CREATE INDEX ix_modules_file_id ON modules(file_id)"))
            conn.execute(text("CREATE INDEX ix_modules_project_id ON modules(project_id)"))
            conn.execute(text("CREATE INDEX ix_modules_module_type ON modules(module_type)"))
            print("   ✓ Created indexes")
        elif old_column_exists:
            print("\n1. Modules table exists with old 'metadata' column - renaming to 'module_metadata'...")
            conn.execute(text("""
                ALTER TABLE modules
                RENAME COLUMN metadata TO module_metadata
            """))
            print("   ✓ Renamed metadata → module_metadata")
        else:
            print("\n1. Modules table already exists with correct schema - skipping")

        # Add MinIO fields to project_files if they don't exist
        print("\n3. Adding MinIO fields to project_files table...")

        # Check for each field individually
        field_check = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='project_files' AND column_name=:col_name
        """)

        fields_to_add = {
            'minio_bucket': 'VARCHAR',
            'minio_key': 'VARCHAR',
            'use_minio': 'BOOLEAN DEFAULT TRUE',
            'content_hash': 'VARCHAR'
        }

        for field_name, field_type in fields_to_add.items():
            result = conn.execute(field_check, {"col_name": field_name}).fetchone()
            if result is None:
                conn.execute(text(f"""
                    ALTER TABLE project_files
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"   ✓ Added column: {field_name}")
            else:
                print(f"   - Column {field_name} already exists")

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("\nDatabase changes:")
    print("  ✓ Modules table created (or already exists)")
    print("  ✓ Indexes created for efficient queries")
    print("  ✓ MinIO storage fields added to project_files")
    print("\nThe system now supports:")
    print("  - Module extraction from Verilog and Python files")
    print("  - MinIO object storage for file content")
    print("  - Automatic module parsing on file save")


if __name__ == "__main__":
    migrate()
