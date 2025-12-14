#!/usr/bin/env python3
"""Initialize database and run migrations."""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


async def init_database():
    """Initialize database with tables and data."""
    print("🔧 Initializing DocuMind database...")

    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database tables created successfully")

        # Run migrations if alembic is available
        try:
            from alembic.config import Config
            from alembic import command

            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            command.upgrade(alembic_cfg, "head")

            print("✅ Database migrations applied successfully")
        except ImportError:
            print("⚠️  Alembic not available, using direct table creation")
        except Exception as e:
            print(f"⚠️  Migration failed: {e}, using direct table creation")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

    print("🎉 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())
