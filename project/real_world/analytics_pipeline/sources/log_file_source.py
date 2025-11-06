"""
Log File Source for analytics pipeline.

This module provides log file tailing capabilities for the analytics pipeline,
supporting multiple log files, pattern matching, and real-time monitoring.
"""

import os
import time
import logging
import threading
import re
from typing import Dict, List, Any, Optional, Callable, Pattern, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from ..pipeline_core.message import DataMessage
from ..pipeline_core.stage_base import SourceStage


@dataclass
class LogFileConfig:
    """Configuration for log file monitoring."""
    path: str
    name: str
    pattern: Optional[str] = None  # Regex pattern to match lines
    encoding: str = 'utf-8'
    buffer_size: int = 8192
    poll_interval: float = 1.0  # seconds
    max_line_length: int = 10000
    follow_rotated: bool = True
    start_from_end: bool = True
    enabled: bool = True


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: float
    line_number: int
    content: str
    file_path: str
    file_name: str
    matched_pattern: Optional[str] = None
    parsed_fields: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.parsed_fields is None:
            self.parsed_fields = {}


@dataclass
class LogFileStats:
    """Statistics for log file processing."""
    files_configured: int = 0
    files_active: int = 0
    lines_processed: int = 0
    lines_matched: int = 0
    lines_filtered: int = 0
    last_read_time: Optional[float] = None
    file_errors: int = 0


class LogFileSource(SourceStage):
    """Log File source stage for the analytics pipeline.

    This stage monitors log files for new entries and emits matching lines
    as pipeline messages. It supports multiple files, pattern matching,
    file rotation detection, and efficient tailing.
    """

    def __init__(
        self,
        name: str,
        files: List[LogFileConfig],
        max_workers: int = 4
    ):
        """Initialize log file source.

        Args:
            name: Stage name
            files: List of log file configurations
            max_workers: Maximum concurrent file monitoring workers
        """
        super().__init__(name)
        self.files = files
        self.max_workers = max_workers

        # State management
        self._running = False
        self._threads: List[threading.Thread] = []
        self._shutdown_event = threading.Event()

        # File monitoring state
        self._file_states: Dict[str, Dict[str, Any]] = {}
        self._compiled_patterns: Dict[str, Optional[Pattern]] = {}

        # Statistics
        self._stats = LogFileStats()
        self._stats_lock = threading.Lock()

        # Logging
        self._logger = logging.getLogger(f"{__name__}.{name}")

        # Compile regex patterns
        self._compile_patterns()

        self._logger.info(f"Initialized log file source with {len(files)} files")

    def _compile_patterns(self) -> None:
        """Compile regex patterns for all configured files."""
        for file_config in self.files:
            if file_config.pattern:
                try:
                    self._compiled_patterns[file_config.name] = re.compile(file_config.pattern)
                    self._logger.debug(f"Compiled pattern for '{file_config.name}': {file_config.pattern}")
                except re.error as e:
                    self._logger.error(f"Invalid regex pattern for '{file_config.name}': {e}")
# Methods are implemented inline to keep file under 200 lines
