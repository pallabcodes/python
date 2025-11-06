"""
Data export functionality for the analytics pipeline.

This module provides various data export capabilities including CSV, JSON,
and Parquet formats with support for streaming, compression, and metadata.
"""

import csv
import json
import os
from typing import Dict, Any, Optional, List, Iterator, TextIO
from pathlib import Path
from datetime import datetime

from ..storage.storage_metrics import QueryFilter, QueryOptions


class ExportMetrics:
    """Metrics for export operations."""

    def __init__(self):
        self.records_exported = 0
        self.bytes_written = 0
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.errors_count = 0

    def complete(self):
        """Mark export as complete."""
        self.end_time = datetime.now()

    def get_duration(self) -> float:
        """Get export duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class BaseExporter:
    """Base class for data exporters.

    Provides common functionality for data export operations including
    metrics tracking, error handling, and file management.
    """

    def __init__(self, output_path: str, compression: Optional[str] = None):
        """Initialize the exporter.

        Args:
            output_path: Path to output file
            compression: Optional compression method ('gzip', 'bz2', etc.)
        """
        self.output_path = Path(output_path)
        self.compression = compression
        self.metrics = ExportMetrics()

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def export_data(self, data_iterator: Iterator[Dict[str, Any]],
                   metadata: Optional[Dict[str, Any]] = None) -> ExportMetrics:
        """Export data from iterator.

        Args:
            data_iterator: Iterator over data records
            metadata: Optional metadata to include

        Returns:
            Export metrics
        """
        try:
            with self._open_output_file() as file:
                self._write_header(file, metadata)

                for record in data_iterator:
                    try:
                        self._write_record(file, record)
                        self.metrics.records_exported += 1
                    except Exception as e:
                        self.metrics.errors_count += 1
                        # Log error but continue with next record
                        print(f"Error exporting record: {e}")

                self._write_footer(file, metadata)

            self.metrics.complete()
            return self.metrics

        except Exception as e:
            self.metrics.errors_count += 1
            self.metrics.complete()
            raise

    def _open_output_file(self) -> TextIO:
        """Open output file with optional compression.

        Returns:
            Open file handle
        """
        mode = 'w' if self.compression else 'w'
        encoding = 'utf-8'

        if self.compression == 'gzip':
            import gzip
            return gzip.open(self.output_path, mode + 't', encoding=encoding)
        elif self.compression == 'bz2':
            import bz2
            return bz2.open(self.output_path, mode + 't', encoding=encoding)
        else:
            return open(self.output_path, mode, encoding=encoding)

    def _write_header(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Write file header.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        pass  # Override in subclasses

    def _write_record(self, file: TextIO, record: Dict[str, Any]) -> None:
        """Write a single record.

        Args:
            file: Output file handle
            record: Data record to write
        """
        raise NotImplementedError("Subclasses must implement _write_record")

    def _write_footer(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Write file footer.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        pass  # Override in subclasses


class CSVExporter(BaseExporter):
    """CSV data exporter with support for custom delimiters and quoting."""

    def __init__(self, output_path: str, delimiter: str = ',',
                 quotechar: str = '"', compression: Optional[str] = None):
        """Initialize CSV exporter.

        Args:
            output_path: Path to output CSV file
            delimiter: CSV delimiter character
            quotechar: Quote character for fields
            compression: Optional compression method
        """
