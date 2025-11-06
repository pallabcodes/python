        Returns:
            Base directory path
        """
        if connection_string.startswith('json:///'):
            return connection_string[8:]  # Remove 'json:///'
        else:
            return connection_string  # Assume it's already a path

    def _get_collection_path(self, collection: str) -> Path:
        """Get the file path for a collection.

        Args:
            collection: Collection name

        Returns:
            Path to collection file
        """
        return Path(self._base_path) / f"{collection}.{self._file_extension}"

    def _load_collection(self, collection: str) -> List[Dict[str, Any]]:
        """Load collection data from file.

        Args:
            collection: Collection name

        Returns:
            List of records
        """
        # Check cache first
        if collection in self._data_cache:
            return self._data_cache[collection][:]

        collection_path = self._get_collection_path(collection)

        if not collection_path.exists():
            return []

        try:
            if self._use_compression:
                with gzip.open(collection_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(collection_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # Ensure it's a list
            if not isinstance(data, list):
                data = [data]

            # Cache the data
            self._data_cache[collection] = data[:]

            return data

        except Exception as e:
            self._logger.warning(f"Error loading collection {collection}: {e}")
            return []

    def _save_collection(self, collection: str, data: List[Dict[str, Any]]) -> None:
        """Save collection data to file.

        Args:
            collection: Collection name
            data: Data to save
        """
        collection_path = self._get_collection_path(collection)

        try:
            if self._use_compression:
                with gzip.open(collection_path, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                with open(collection_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)

        except Exception as e:
            self._logger.error(f"Error saving collection {collection}: {e}")
            raise

    def _apply_filters(self, data: List[Dict[str, Any]],
                      filters: Optional[List[QueryFilter]] = None) -> List[Dict[str, Any]]:
        """Apply filters to data.

        Args:
            data: Data to filter
            filters: List of filters to apply

        Returns:
            Filtered data
        """
        if not filters:
            return data[:]

        filtered_data = data[:]

        for filter_obj in filters:
            filtered_data = [record for record in filtered_data
                           if self._matches_filter(record, filter_obj)]

        return filtered_data

    def _matches_filter(self, record: Dict[str, Any], filter_obj: QueryFilter) -> bool:
        """Check if a record matches a filter.

        Args:
            record: Record to check
            filter_obj: Filter to apply

        Returns:
            True if record matches filter
        """
        value = self._get_nested_value(record, filter_obj.field)
        if value is None:
            return False

        operator = filter_obj.operator.lower()

        if operator == 'eq':
            return value == filter_obj.value
        elif operator == 'ne':
            return value != filter_obj.value
        elif operator == 'gt':
            return value > filter_obj.value
        elif operator == 'gte':
            return value >= filter_obj.value
        elif operator == 'lt':
            return value < filter_obj.value
        elif operator == 'lte':
            return value <= filter_obj.value
        elif operator == 'in':
            return value in filter_obj.value
        elif operator == 'contains':
            return str(filter_obj.value) in str(value)
        elif operator == 'regex':
            import re
            return bool(re.search(str(filter_obj.value), str(value)))
        else:
            return True

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get a nested value from data using dot notation.

        Args:
            data: Data dictionary
            field_path: Field path (e.g., 'metadata.timestamp')

        Returns:
            Field value or None
        """
        try:
            current = data
            for part in field_path.split('.'):
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current
        except Exception:
            return None

    def _create_connection(self) -> Any:
        """Create a connection (no-op for file-based storage)."""
        return None

    def _close_connection(self, connection: Any) -> None:
        """Close a connection (no-op for file-based storage)."""
        pass
