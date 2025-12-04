"""
Script to verify that all models are properly registered with SQLAlchemy metadata.
Run this script to check if all tables would be created correctly in tests.
"""
import asyncio
import os
import sys

from sqlalchemy import inspect

# Set the environment to test
os.environ["APP_ENV"] = "test"

# Add the project root to the path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after setting environment
from app.config.database import Base, engine


async def check_tables() -> tuple[int, int]:
    """Check if all tables are registered with SQLAlchemy metadata."""
    print("Checking tables registered in SQLAlchemy metadata...")

    # Print all tables in metadata
    tables = Base.metadata.tables.keys()
    print(f"Found {len(tables)} tables in SQLAlchemy metadata:")
    for table in tables:
        print(f"  - {table}")

    print("\nChecking if tables exist in database...")
    async with engine.begin() as conn:
        # Check if tables already exist in the database
        inspector = inspect(conn)
        existing_tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        print(f"Found {len(existing_tables)} existing tables in database:")
        for table in existing_tables:
            print(f"  - {table}")

        print("\nCreating all tables from metadata...")
        # Create all tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # Check created tables
        inspector = inspect(conn)
        created_tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        print(f"Created {len(created_tables)} tables:")
        for table in created_tables:
            print(f"  - {table}")

    return len(tables), len(created_tables)


if __name__ == "__main__":
    metadata_count, created_count = asyncio.run(check_tables())

    if metadata_count == created_count:
        print(f"\n✅ Success! All {metadata_count} tables were properly registered " f"and created.")
        sys.exit(0)
    else:
        print(f"\n❌ Error! Only {created_count} tables were created out of " f"{metadata_count} registered.")
        sys.exit(1)
