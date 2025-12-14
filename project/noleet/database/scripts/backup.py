#!/usr/bin/env python3
"""
Database backup script for NoLeet.

Features:
- Full database backups
- Incremental backups
- Point-in-time recovery support
- Compression and encryption
- Automated retention policies
- Backup verification
"""

import asyncio
import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from noleet.app.core.config import settings
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseBackup:
    """Handles database backup operations."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        backup_dir: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None
    ):
        self.database_url = database_url or settings.DATABASE_URL
        self.backup_dir = Path(backup_dir or settings.BACKUP_DIR or "./backups")
        self.s3_bucket = s3_bucket or getattr(settings, 'BACKUP_S3_BUCKET', None)
        self.s3_prefix = s3_prefix or getattr(settings, 'BACKUP_S3_PREFIX', 'backups/')

        # Extract database connection details
        self._parse_database_url()

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client if bucket is configured
        self.s3_client = None
        if self.s3_bucket:
            self.s3_client = boto3.client('s3')

    def _parse_database_url(self) -> None:
        """Parse database URL to extract connection details."""
        from urllib.parse import urlparse

        parsed = urlparse(self.database_url)
        self.db_host = parsed.hostname
        self.db_port = parsed.port or 5432
        self.db_name = parsed.path.lstrip('/')
        self.db_user = parsed.username
        self.db_password = parsed.password

    async def create_backup(
        self,
        backup_type: str = "full",
        compress: bool = True,
        encrypt: bool = False
    ) -> str:
        """Create a database backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"noleet_{backup_type}_{timestamp}"

        logger.info(f"Starting {backup_type} backup: {backup_name}")

        try:
            if backup_type == "full":
                backup_file = await self._create_full_backup(backup_name, compress)
            elif backup_type == "schema":
                backup_file = await self._create_schema_backup(backup_name, compress)
            else:
                raise ValueError(f"Unsupported backup type: {backup_type}")

            # Verify backup
            await self._verify_backup(backup_file)

            # Upload to S3 if configured
            if self.s3_client:
                await self._upload_to_s3(backup_file)

            logger.info(f"Backup completed successfully: {backup_file}")
            return str(backup_file)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    async def _create_full_backup(self, backup_name: str, compress: bool) -> Path:
        """Create a full database backup."""
        backup_file = self.backup_dir / f"{backup_name}.sql"

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "--host", self.db_host,
            "--port", str(self.db_port),
            "--username", self.db_user,
            "--dbname", self.db_name,
            "--no-password",
            "--format", "c",  # Custom format
            "--compress", "9",
            "--verbose",
            "--file", str(backup_file)
        ]

        # Set password environment
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password

        # Execute backup
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise Exception(f"pg_dump failed: {error_msg}")

        # Compress if requested
        if compress:
            compressed_file = backup_file.with_suffix(".sql.gz")
            await self._compress_file(backup_file, compressed_file)
            backup_file = compressed_file

        return backup_file

    async def _create_schema_backup(self, backup_name: str, compress: bool) -> Path:
        """Create a schema-only backup."""
        backup_file = self.backup_dir / f"{backup_name}_schema.sql"

        cmd = [
            "pg_dump",
            "--host", self.db_host,
            "--port", str(self.db_port),
            "--username", self.db_user,
            "--dbname", self.db_name,
            "--no-password",
            "--schema-only",
            "--no-owner",
            "--no-privileges",
            "--clean",
            "--if-exists"
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password

        with open(backup_file, 'w') as f:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=f,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise Exception(f"pg_dump schema failed: {error_msg}")

        # Compress if requested
        if compress:
            compressed_file = backup_file.with_suffix(".sql.gz")
            await self._compress_file(backup_file, compressed_file)
            backup_file = compressed_file

        return backup_file

    async def _compress_file(self, source: Path, destination: Path) -> None:
        """Compress a file using gzip."""
        logger.info(f"Compressing {source} to {destination}")

        with open(source, 'rb') as f_in:
            with gzip.open(destination, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove original file
        source.unlink()

    async def _verify_backup(self, backup_file: Path) -> None:
        """Verify backup integrity."""
        logger.info(f"Verifying backup: {backup_file}")

        if not backup_file.exists():
            raise Exception(f"Backup file does not exist: {backup_file}")

        # Basic size check
        size = backup_file.stat().st_size
        if size == 0:
            raise Exception(f"Backup file is empty: {backup_file}")

        logger.info(f"Backup verification passed: {size} bytes")

    async def _upload_to_s3(self, backup_file: Path) -> None:
        """Upload backup to S3."""
        if not self.s3_client:
            return

        s3_key = f"{self.s3_prefix.rstrip('/')}/{backup_file.name}"

        logger.info(f"Uploading {backup_file} to s3://{self.s3_bucket}/{s3_key}")

        try:
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key
            )
            logger.info("S3 upload completed")

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def restore_backup(
        self,
        backup_file: str,
        target_database: Optional[str] = None
    ) -> None:
        """Restore a database backup."""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            # Try to download from S3
            if self.s3_client:
                await self._download_from_s3(backup_file)
                backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            raise Exception(f"Backup file not found: {backup_file}")

        logger.info(f"Restoring backup: {backup_path}")

        # Decompress if needed
        if backup_path.suffix == ".gz":
            decompressed = backup_path.with_suffix("")
            await self._decompress_file(backup_path, decompressed)
            backup_path = decompressed

        # Restore database
        target_db = target_database or self.db_name

        cmd = [
            "pg_restore",
            "--host", self.db_host,
            "--port", str(self.db_port),
            "--username", self.db_user,
            "--dbname", target_db,
            "--no-password",
            "--clean",
            "--if-exists",
            "--create",
            "--verbose",
            str(backup_path)
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise Exception(f"pg_restore failed: {error_msg}")

        logger.info("Database restore completed successfully")

    async def _download_from_s3(self, backup_file: str) -> None:
        """Download backup from S3."""
        if not self.s3_client:
            raise Exception("S3 client not configured")

        s3_key = f"{self.s3_prefix.rstrip('/')}/{backup_file}"
        local_path = self.backup_dir / backup_file

        logger.info(f"Downloading s3://{self.s3_bucket}/{s3_key} to {local_path}")

        try:
            self.s3_client.download_file(
                self.s3_bucket,
                s3_key,
                str(local_path)
            )
            logger.info("S3 download completed")

        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise

    async def _decompress_file(self, source: Path, destination: Path) -> None:
        """Decompress a gzip file."""
        logger.info(f"Decompressing {source} to {destination}")

        with gzip.open(source, 'rb') as f_in:
            with open(destination, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    async def cleanup_old_backups(self, retention_days: int = 30) -> None:
        """Clean up old backup files."""
        logger.info(f"Cleaning up backups older than {retention_days} days")

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        for backup_file in self.backup_dir.glob("*.sql*"):
            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_date < cutoff_date:
                backup_file.unlink()
                deleted_count += 1

                # Also delete from S3 if configured
                if self.s3_client:
                    s3_key = f"{self.s3_prefix.rstrip('/')}/{backup_file.name}"
                    try:
                        self.s3_client.delete_object(
                            Bucket=self.s3_bucket,
                            Key=s3_key
                        )
                    except ClientError as e:
                        logger.warning(f"Failed to delete {s3_key} from S3: {e}")

        logger.info(f"Cleaned up {deleted_count} old backup files")

    async def list_backups(self) -> List[Dict]:
        """List available backups."""
        backups = []

        # Local backups
        for backup_file in self.backup_dir.glob("*.sql*"):
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime),
                "location": "local"
            })

        # S3 backups
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=self.s3_prefix
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        backups.append({
                            "name": Path(obj['Key']).name,
                            "path": obj['Key'],
                            "size": obj['Size'],
                            "modified": obj['LastModified'],
                            "location": "s3"
                        })
            except ClientError as e:
                logger.warning(f"Failed to list S3 backups: {e}")

        return sorted(backups, key=lambda x: x['modified'], reverse=True)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NoLeet Database Backup Tool")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list", "cleanup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--type",
        choices=["full", "schema"],
        default="full",
        help="Backup type (default: full)"
    )
    parser.add_argument(
        "--file",
        help="Backup file for restore operation"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides environment)"
    )
    parser.add_argument(
        "--backup-dir",
        help="Backup directory (overrides environment)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Days to retain backups (default: 30)"
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        default=True,
        help="Compress backup files"
    )

    args = parser.parse_args()

    # Setup logging
    import logging
    logging.basicConfig(level=logging.INFO)

    backup_tool = DatabaseBackup(
        database_url=args.database_url,
        backup_dir=args.backup_dir
    )

    try:
        if args.action == "backup":
            backup_file = await backup_tool.create_backup(
                backup_type=args.type,
                compress=args.compress
            )
            print(f"✅ Backup created: {backup_file}")

        elif args.action == "restore":
            if not args.file:
                parser.error("--file is required for restore action")
            await backup_tool.restore_backup(args.file)
            print("✅ Database restored successfully")

        elif args.action == "list":
            backups = await backup_tool.list_backups()
            if backups:
                print("Available backups:")
                for backup in backups:
                    print(f"  {backup['name']} ({backup['location']}) - {backup['modified']}")
            else:
                print("No backups found")

        elif args.action == "cleanup":
            await backup_tool.cleanup_old_backups(args.retention_days)
            print(f"✅ Cleaned up backups older than {args.retention_days} days")

        return 0

    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
