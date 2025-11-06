            return

        try:
            import pandas as pd
            import pyarrow as pa
            from pyarrow import parquet

            # Convert to DataFrame
            df = pd.DataFrame(self._buffer)

            # Convert to PyArrow table
            table = pa.Table.from_pandas(df)

            # Write to Parquet
            parquet.write_table(
                table,
                self.output_path,
                compression=self.compression,
                use_dictionary=True,
                row_group_size=self.row_group_size
            )

            self._buffer.clear()

        except ImportError:
            raise ImportError("Parquet export requires pandas and pyarrow: pip install pandas pyarrow")


class ExportManager:
    """Manager for coordinating multiple export operations."""

    def __init__(self):
        self.exporters = {
            'csv': CSVExporter,
            'json': JSONExporter,
            'parquet': ParquetExporter
        }

    def create_exporter(self, format_type: str, output_path: str, **kwargs) -> BaseExporter:
        """Create an exporter instance.

        Args:
            format_type: Export format ('csv', 'json', 'parquet')
            output_path: Output file path
            **kwargs: Format-specific arguments

        Returns:
            Configured exporter instance

        Raises:
            ValueError: If format type is not supported
        """
        if format_type not in self.exporters:
            raise ValueError(f"Unsupported export format: {format_type}")

        exporter_class = self.exporters[format_type]
        return exporter_class(output_path, **kwargs)

    def export_from_storage(self, storage_backend, collection: str,
                          format_type: str, output_path: str,
                          filters: Optional[List[QueryFilter]] = None,
                          options: Optional[QueryOptions] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          **export_kwargs) -> ExportMetrics:
        """Export data from storage backend.

        Args:
            storage_backend: Storage backend instance
            collection: Collection/table to export
            format_type: Export format
            output_path: Output file path
            filters: Query filters
            options: Query options
            metadata: Export metadata
            **export_kwargs: Format-specific arguments

        Returns:
            Export metrics
        """
        # Query data from storage
        data_iterator = storage_backend.query(collection, filters, options)

        # Create exporter
        exporter = self.create_exporter(format_type, output_path, **export_kwargs)

        # Export data
        return exporter.export_data(data_iterator, metadata)
