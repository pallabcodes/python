        """
        super().__init__(output_path, compression)
        self.delimiter = delimiter
        self.quotechar = quotechar
        self._fieldnames: Optional[List[str]] = None

    def _write_header(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Write CSV header.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        # Write metadata as comments if provided
        if metadata:
            file.write(f"# Export metadata: {json.dumps(metadata)}\n")
            file.write(f"# Generated at: {datetime.now().isoformat()}\n")

    def _write_record(self, file: TextIO, record: Dict[str, Any]) -> None:
        """Write CSV record.

        Args:
            file: Output file handle
            record: Data record to write
        """
        # Initialize fieldnames on first record
        if self._fieldnames is None:
            self._fieldnames = list(record.keys())
            # Write header row
            writer = csv.DictWriter(file, fieldnames=self._fieldnames,
                                  delimiter=self.delimiter, quotechar=self.quotechar,
                                  quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

        # Write data row
        writer = csv.DictWriter(file, fieldnames=self._fieldnames,
                              delimiter=self.delimiter, quotechar=self.quotechar,
                              quoting=csv.QUOTE_MINIMAL)
        writer.writerow(record)


class JSONExporter(BaseExporter):
    """JSON data exporter with support for JSON Lines and array formats."""

    def __init__(self, output_path: str, format_type: str = 'array',
                 pretty: bool = False, compression: Optional[str] = None):
        """Initialize JSON exporter.

        Args:
            output_path: Path to output JSON file
            format_type: 'array' for JSON array, 'lines' for JSON Lines
            pretty: Whether to pretty-print JSON
            compression: Optional compression method
        """
        super().__init__(output_path, compression)
        self.format_type = format_type
        self.pretty = pretty
        self._first_record = True

    def _write_header(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Write JSON header.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        if self.format_type == 'array':
            # Start JSON array
            file.write('[\n')
        elif self.format_type == 'object':
            # Start JSON object with metadata
            data = {'metadata': metadata or {}, 'data': []}
            json.dump(data, file, indent=2 if self.pretty else None, default=str)
            file.write('\n"data": [\n')
            self._first_record = True

    def _write_record(self, file: TextIO, record: Dict[str, Any]) -> None:
        """Write JSON record.

        Args:
            file: Output file handle
            record: Data record to write
        """
        if self.format_type == 'lines':
            # JSON Lines format
            json.dump(record, file, default=str)
            file.write('\n')
        else:
            # Array format
            if not self._first_record:
                file.write(',\n')
            json.dump(record, file, indent=2 if self.pretty else None, default=str)
            self._first_record = False

    def _write_footer(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Write JSON footer.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        if self.format_type == 'array':
            file.write('\n]\n')
        elif self.format_type == 'object':
            file.write('\n]}\n')


class ParquetExporter(BaseExporter):
    """Apache Parquet data exporter for efficient columnar storage."""

    def __init__(self, output_path: str, row_group_size: int = 10000,
                 compression: str = 'snappy'):
        """Initialize Parquet exporter.

        Args:
            output_path: Path to output Parquet file
            row_group_size: Number of rows per row group
            compression: Compression codec ('snappy', 'gzip', 'brotli', etc.)
        """
        super().__init__(output_path, None)  # Parquet handles its own compression
        self.row_group_size = row_group_size
        self.compression = compression
        self._buffer: List[Dict[str, Any]] = []

    def _write_record(self, file: TextIO, record: Dict[str, Any]) -> None:
        """Buffer record for batch writing.

        Args:
            file: Output file handle (ignored for Parquet)
            record: Data record to buffer
        """
        self._buffer.append(record)

        # Write batch when buffer is full
        if len(self._buffer) >= self.row_group_size:
            self._flush_buffer()

    def _write_footer(self, file: TextIO, metadata: Optional[Dict[str, Any]]) -> None:
        """Flush any remaining buffered records.

        Args:
            file: Output file handle
            metadata: Optional metadata
        """
        if self._buffer:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffered records to Parquet file."""
        if not self._buffer:
