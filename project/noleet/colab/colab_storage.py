"""Google Colab storage handling."""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union


class ColabStorage:
    """Handles storage operations in Google Colab environment."""

    def __init__(
        self,
        local_base_dir: Optional[Path] = None,
        drive_base_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Colab storage handler.

        Args:
            local_base_dir: Local storage directory (defaults to /content/noleet)
            drive_base_dir: Google Drive base directory (defaults to /content/drive/MyDrive/noleet)
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)

        # Set default directories
        self._local_base_dir = local_base_dir or Path("/content/noleet")
        self._drive_base_dir = drive_base_dir or "/content/drive/MyDrive/noleet"

        # Storage preferences
        self._prefer_drive = True  # Prefer Drive for persistence
        self._auto_sync = True     # Auto-sync between local and Drive

        # Ensure directories exist
        self._setup_directories()

    def get_storage_path(self, relative_path: str, prefer_drive: Optional[bool] = None) -> Path:
        """
        Get the appropriate storage path for a file.

        Args:
            relative_path: Relative path from storage root
            prefer_drive: Whether to prefer Drive storage

        Returns:
            Absolute path to the file
        """
        prefer_drive = prefer_drive if prefer_drive is not None else self._prefer_drive

        if prefer_drive and self.is_drive_available():
            base_path = Path(self._drive_base_dir)
        else:
            base_path = self._local_base_dir

        return base_path / relative_path

    def read_file(self, relative_path: str, prefer_drive: Optional[bool] = None) -> Optional[str]:
        """
        Read file content from storage.

        Args:
            relative_path: Relative path to file
            prefer_drive: Whether to prefer Drive storage

        Returns:
            File content or None if not found
        """
        file_path = self.get_storage_path(relative_path, prefer_drive)

        # Try preferred location first
        if file_path.exists():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception as e:
                self._logger.error(f"Failed to read {file_path}: {e}")

        # If preferred location failed and Drive is available, try alternative
        if prefer_drive and self.is_drive_available():
            alt_path = self.get_storage_path(relative_path, prefer_drive=False)
            if alt_path.exists():
                try:
                    return alt_path.read_text(encoding="utf-8")
                except Exception as e:
                    self._logger.error(f"Failed to read {alt_path}: {e}")
        elif not prefer_drive and self.is_drive_available():
            alt_path = self.get_storage_path(relative_path, prefer_drive=True)
            if alt_path.exists():
                try:
                    return alt_path.read_text(encoding="utf-8")
                except Exception as e:
                    self._logger.error(f"Failed to read {alt_path}: {e}")

        return None

    def write_file(
        self,
        relative_path: str,
        content: str,
        prefer_drive: Optional[bool] = None
    ) -> bool:
        """
        Write file content to storage.

        Args:
            relative_path: Relative path to file
            content: File content
            prefer_drive: Whether to prefer Drive storage

        Returns:
            True if successful
        """
        file_path = self.get_storage_path(relative_path, prefer_drive)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            # Auto-sync if enabled
            if self._auto_sync:
                self._sync_file(relative_path, prefer_drive)

            return True

        except Exception as e:
            self._logger.error(f"Failed to write {file_path}: {e}")
            return False

    def file_exists(self, relative_path: str, prefer_drive: Optional[bool] = None) -> bool:
        """
        Check if file exists in storage.

        Args:
            relative_path: Relative path to file
            prefer_drive: Whether to prefer Drive storage

        Returns:
            True if file exists
        """
        file_path = self.get_storage_path(relative_path, prefer_drive)
        return file_path.exists()

    def list_files(self, relative_dir: str = "", prefer_drive: Optional[bool] = None) -> list[str]:
        """
        List files in storage directory.

        Args:
            relative_dir: Relative directory path
            prefer_drive: Whether to prefer Drive storage

        Returns:
            List of file names
        """
        dir_path = self.get_storage_path(relative_dir, prefer_drive)

        if not dir_path.exists() or not dir_path.is_dir():
            return []

        try:
            return [f.name for f in dir_path.iterdir() if f.is_file()]
        except Exception as e:
            self._logger.error(f"Failed to list files in {dir_path}: {e}")
            return []

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage information.

        Returns:
            Dictionary with storage details
        """
        info = {
            "local_available": self._local_base_dir.exists(),
            "drive_available": self.is_drive_available(),
            "prefer_drive": self._prefer_drive,
            "auto_sync": self._auto_sync
        }

        # Get local storage info
        if info["local_available"]:
            try:
                stat = os.statvfs(str(self._local_base_dir))
                info["local_free_gb"] = round(stat.f_bavail * stat.f_frsize / (1024**3), 2)
            except OSError:
                pass

        # Get Drive storage info
        if info["drive_available"]:
            try:
                stat = os.statvfs(self._drive_base_dir)
                info["drive_free_gb"] = round(stat.f_bavail * stat.f_frsize / (1024**3), 2)
            except OSError:
                pass

        return info

    def is_drive_available(self) -> bool:
        """
        Check if Google Drive is available.

        Returns:
            True if Drive is mounted and accessible
        """
        return os.path.exists(self._drive_base_dir)

    def mount_drive(self) -> bool:
        """
        Mount Google Drive (Colab-specific).

        Returns:
            True if mounting was attempted (user interaction may be required)
        """
        try:
            from google.colab import drive
            drive.mount('/content/drive')
            self._logger.info("Google Drive mount initiated")
            return True
        except ImportError:
            self._logger.warning("Not running in Colab, cannot mount Drive")
            return False
        except Exception as e:
            self._logger.error(f"Drive mounting failed: {e}")
            return False

    def _setup_directories(self):
        """Setup necessary directories."""
        try:
            self._local_base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._logger.error(f"Failed to create local directory {self._local_base_dir}: {e}")

    def _sync_file(self, relative_path: str, from_drive: bool):
        """
        Sync file between local and Drive storage.

        Args:
            relative_path: Relative path to file
            from_drive: Whether syncing from Drive to local (or vice versa)
        """
        if not self.is_drive_available():
            return

        source_path = self.get_storage_path(relative_path, prefer_drive=from_drive)
        dest_path = self.get_storage_path(relative_path, prefer_drive=not from_drive)

        try:
            if source_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                self._logger.debug(f"Synced {relative_path} {'from' if from_drive else 'to'} Drive")
        except Exception as e:
            self._logger.error(f"Failed to sync {relative_path}: {e}")

    def backup_to_drive(self, relative_path: str) -> bool:
        """
        Backup file to Google Drive.

        Args:
            relative_path: Relative path to file

        Returns:
            True if backup successful
        """
        if not self.is_drive_available():
            return False

        return self._sync_file(relative_path, from_drive=False)

    def restore_from_drive(self, relative_path: str) -> bool:
        """
        Restore file from Google Drive.

        Args:
            relative_path: Relative path to file

        Returns:
            True if restore successful
        """
        if not self.is_drive_available():
            return False

        return self._sync_file(relative_path, from_drive=True)

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary files older than specified hours.

        Args:
            older_than_hours: Age threshold in hours
        """
        import time

        cutoff_time = time.time() - (older_than_hours * 3600)

        for base_dir in [self._local_base_dir, Path(self._drive_base_dir)]:
            if base_dir.exists():
                try:
                    for file_path in base_dir.rglob("*"):
                        if file_path.is_file():
                            if file_path.stat().st_mtime < cutoff_time:
                                file_path.unlink()
                                self._logger.debug(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    self._logger.error(f"Cleanup failed for {base_dir}: {e}")

    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get storage recommendations for Colab environment.

        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "mount_drive": False,
            "use_drive_for_large_files": False,
            "cleanup_schedule": "daily",
            "backup_important_files": False
        }

        if not self.is_drive_available():
            recommendations["mount_drive"] = True

        storage_info = self.get_storage_info()
        local_free = storage_info.get("local_free_gb", 0)
        drive_free = storage_info.get("drive_free_gb", 0)

        if drive_free > local_free:
            recommendations["use_drive_for_large_files"] = True

        recommendations["backup_important_files"] = drive_free > 0

        return recommendations
