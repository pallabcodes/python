#!/usr/bin/env python3
"""
Database initialization script for NoLeet.

This script handles:
1. Database creation and setup
2. Initial data seeding
3. Migration execution
4. Health checks
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from noleet.app.core.config import settings
from noleet.app.core.logging import get_logger
from noleet.app.models import Base

logger = get_logger(__name__)


class DatabaseInitializer:
    """Handles database initialization and setup."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = None
        self.async_session = None

    async def initialize_database(self) -> None:
        """Initialize the database with all required setup."""
        try:
            logger.info("Starting database initialization...")

            # Create engine
            self.engine = create_async_engine(
                self.database_url,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_recycle=300
            )

            # Create async session factory
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Test connection
            await self._test_connection()

            # Create all tables
            await self._create_tables()

            # Run migrations if needed
            await self._run_migrations()

            # Seed initial data
            await self._seed_initial_data()

            # Run health checks
            await self._run_health_checks()

            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _test_connection(self) -> None:
        """Test database connection."""
        logger.info("Testing database connection...")

        async with self.engine.begin() as conn:
            result = await conn.execute(sa.text("SELECT 1"))
            if result.fetchone()[0] != 1:
                raise Exception("Database connection test failed")

        logger.info("Database connection test passed")

    async def _create_tables(self) -> None:
        """Create all database tables."""
        logger.info("Creating database tables...")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    async def _run_migrations(self) -> None:
        """Run database migrations."""
        logger.info("Checking for pending migrations...")

        # Import alembic here to avoid circular imports
        from alembic.config import Config
        from alembic import command

        # Configure alembic
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "database/migrations/alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        # Check current revision
        try:
            current_rev = command.current(alembic_cfg)
            logger.info(f"Current migration revision: {current_rev}")

            # Upgrade to latest
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations executed successfully")

        except Exception as e:
            logger.warning(f"Migration check failed: {e}")

    async def _seed_initial_data(self) -> None:
        """Seed initial data into the database."""
        logger.info("Seeding initial data...")

        async with self.async_session() as session:
            try:
                # Seed categories
                await self._seed_categories(session)

                # Seed default admin user
                await self._seed_admin_user(session)

                # Seed default agents
                await self._seed_agents(session)

                await session.commit()
                logger.info("Initial data seeded successfully")

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to seed initial data: {e}")
                raise

    async def _seed_categories(self, session: AsyncSession) -> None:
        """Seed initial categories."""
        from noleet.app.models.category import Category

        categories_data = [
            {"name": "Algorithms", "slug": "algorithms", "description": "Algorithm design and analysis"},
            {"name": "Data Structures", "slug": "data-structures", "description": "Fundamental data structures"},
            {"name": "Dynamic Programming", "slug": "dynamic-programming", "description": "Dynamic programming problems"},
            {"name": "Graph Theory", "slug": "graph-theory", "description": "Graph algorithms and problems"},
            {"name": "String Algorithms", "slug": "string-algorithms", "description": "String manipulation and algorithms"},
            {"name": "Mathematics", "slug": "mathematics", "description": "Mathematical problems and concepts"},
            {"name": "System Design", "slug": "system-design", "description": "Large-scale system design"},
            {"name": "Database", "slug": "database", "description": "Database design and optimization"},
        ]

        for category_data in categories_data:
            # Check if category exists
            result = await session.execute(
                sa.select(Category).where(Category.slug == category_data["slug"])
            )
            if not result.fetchone():
                category = Category(**category_data)
                session.add(category)
                logger.debug(f"Added category: {category_data['name']}")

    async def _seed_admin_user(self, session: AsyncSession) -> None:
        """Seed default admin user."""
        from noleet.app.models.user import User
        from noleet.app.core.security import get_password_hash

        # Check if admin user exists
        result = await session.execute(
            sa.select(User).where(User.username == "admin")
        )
        if not result.fetchone():
            admin_user = User(
                username="admin",
                email="admin@noleet.ai",
                hashed_password=get_password_hash("admin123!@#"),
                role="admin",
                is_active=True,
                is_verified=True
            )
            session.add(admin_user)
            logger.info("Created default admin user: admin/admin123!@#")

    async def _seed_agents(self, session: AsyncSession) -> None:
        """Seed default agents."""
        from noleet.app.models.agent import Agent

        agents_data = [
            {
                "name": "project_recommendation_agent",
                "type": "recommendation",
                "config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            {
                "name": "question_analysis_agent",
                "type": "analysis",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            },
            {
                "name": "sentiment_analysis_agent",
                "type": "analysis",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1,
                    "max_tokens": 200
                }
            }
        ]

        for agent_data in agents_data:
            # Check if agent exists
            result = await session.execute(
                sa.select(Agent).where(Agent.name == agent_data["name"])
            )
            if not result.fetchone():
                agent = Agent(**agent_data, status="idle")
                session.add(agent)
                logger.debug(f"Added agent: {agent_data['name']}")

    async def _run_health_checks(self) -> None:
        """Run database health checks."""
        logger.info("Running database health checks...")

        async with self.engine.begin() as conn:
            # Check table existence
            tables_to_check = [
                "users", "categories", "projects", "questions",
                "agents", "research_papers"
            ]

            for table in tables_to_check:
                result = await conn.execute(sa.text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    f"WHERE table_name = '{table}')"
                ))
                if not result.fetchone()[0]:
                    raise Exception(f"Required table '{table}' does not exist")

            # Check enum types
            enums_to_check = [
                "user_role", "difficulty_level", "question_status",
                "project_status", "agent_status"
            ]

            for enum_type in enums_to_check:
                result = await conn.execute(sa.text(
                    "SELECT EXISTS (SELECT 1 FROM pg_type "
                    f"WHERE typname = '{enum_type}')"
                ))
                if not result.fetchone()[0]:
                    raise Exception(f"Required enum type '{enum_type}' does not exist")

        logger.info("Database health checks passed")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.engine:
            await self.engine.dispose()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize NoLeet database")
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides environment variable)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-initialization (drops existing data)"
    )

    args = parser.parse_args()

    # Setup logging
    import logging
    logging.basicConfig(level=logging.INFO)

    initializer = DatabaseInitializer(args.database_url)

    try:
        await initializer.initialize_database()
        logger.info("🎉 Database initialization completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return 1
    finally:
        await initializer.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
