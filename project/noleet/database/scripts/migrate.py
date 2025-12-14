#!/usr/bin/env python3
"""
Database migration script for NoLeet.

This script provides a safe way to run database migrations
during deployment and updates.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from noleet.app.core.config import settings
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseMigrator:
    """Handles database migrations using Alembic."""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.alembic_cfg = self._configure_alembic()

    def _configure_alembic(self) -> Config:
        """Configure Alembic with proper settings."""
        alembic_cfg = Config()
        alembic_cfg.set_main_option(
            "script_location",
            str(project_root / "database" / "migrations" / "alembic")
        )
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        # Set other alembic options
        alembic_cfg.set_main_option("logging_level", "INFO")
        alembic_cfg.set_main_option("max_overflow", "20")
        alembic_cfg.set_main_option("pool_size", "10")

        return alembic_cfg

    def check_migration_status(self) -> dict:
        """Check the current migration status."""
        try:
            # Get current revision
            current_rev = command.current(self.alembic_cfg)

            # Get head revision
            head_rev = command.heads(self.alembic_cfg)

            # Check for pending migrations
            pending = []
            try:
                command.check(self.alembic_cfg)
                has_pending = False
            except SystemExit:
                has_pending = True
                # Get list of pending migrations
                from alembic.script import ScriptDirectory
                script_dir = ScriptDirectory.from_config(self.alembic_cfg)
                pending = [
                    rev.revision
                    for rev in script_dir.iterate_revisions(current_rev, head_rev)
                ]

            return {
                "current_revision": current_rev,
                "head_revision": head_rev,
                "has_pending_migrations": has_pending,
                "pending_revisions": pending
            }

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {
                "error": str(e),
                "current_revision": None,
                "head_revision": None,
                "has_pending_migrations": False,
                "pending_revisions": []
            }

    def upgrade_database(self, target_revision: str = "head") -> None:
        """Upgrade database to target revision."""
        logger.info(f"Upgrading database to revision: {target_revision}")

        try:
            command.upgrade(self.alembic_cfg, target_revision)
            logger.info("Database upgrade completed successfully")

        except Exception as e:
            logger.error(f"Database upgrade failed: {e}")
            raise

    def downgrade_database(self, target_revision: str) -> None:
        """Downgrade database to target revision."""
        logger.warning(f"Downgrading database to revision: {target_revision}")

        try:
            command.downgrade(self.alembic_cfg, target_revision)
            logger.warning("Database downgrade completed")

        except Exception as e:
            logger.error(f"Database downgrade failed: {e}")
            raise

    def create_migration(self, message: str, auto_generate: bool = True) -> None:
        """Create a new migration file."""
        logger.info(f"Creating migration: {message}")

        try:
            if auto_generate:
                command.revision(self.alembic_cfg, message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message)
            logger.info("Migration file created successfully")

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise

    def show_migration_history(self) -> None:
        """Show migration history."""
        try:
            command.history(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Failed to show migration history: {e}")
            raise

    def validate_migrations(self) -> bool:
        """Validate migration files."""
        try:
            from alembic.script import ScriptDirectory

            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            script_dir.walk_revisions()
            logger.info("Migration validation passed")
            return True

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NoLeet Database Migration Tool")
    parser.add_argument(
        "action",
        choices=["status", "upgrade", "downgrade", "create", "history", "validate"],
        help="Migration action to perform"
    )
    parser.add_argument(
        "--revision",
        help="Target revision for upgrade/downgrade"
    )
    parser.add_argument(
        "--message",
        help="Message for new migration"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides environment)"
    )

    args = parser.parse_args()

    # Setup logging
    import logging
    logging.basicConfig(level=logging.INFO)

    migrator = DatabaseMigrator(database_url=args.database_url)

    try:
        if args.action == "status":
            status = migrator.check_migration_status()
            print("Migration Status:")
            print(f"  Current: {status['current_revision']}")
            print(f"  Head: {status['head_revision']}")
            print(f"  Pending: {status['has_pending_migrations']}")
            if status['pending_revisions']:
                print(f"  Pending revisions: {', '.join(status['pending_revisions'])}")
            if status.get('error'):
                print(f"  Error: {status['error']}")
                return 1

        elif args.action == "upgrade":
            target = args.revision or "head"
            migrator.upgrade_database(target)
            print(f"✅ Database upgraded to {target}")

        elif args.action == "downgrade":
            if not args.revision:
                parser.error("--revision is required for downgrade action")
            migrator.downgrade_database(args.revision)
            print(f"⚠️  Database downgraded to {args.revision}")

        elif args.action == "create":
            if not args.message:
                parser.error("--message is required for create action")
            migrator.create_migration(args.message)
            print("✅ Migration file created")

        elif args.action == "history":
            migrator.show_migration_history()

        elif args.action == "validate":
            if migrator.validate_migrations():
                print("✅ Migration validation passed")
            else:
                print("❌ Migration validation failed")
                return 1

        return 0

    except Exception as e:
        logger.error(f"❌ Migration operation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
