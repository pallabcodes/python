        except Exception as e:
            self._update_metrics('write', False, 0, __import__('time').time() - start_time)
            self._logger.error(f"Error in batch store to {collection}: {e}")
            raise

    def retrieve(self, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single record by ID.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            Retrieved data or None
        """
        start_time = __import__('time').time()

        try:
            collection_data = self._load_collection(collection)

            for record in collection_data:
                if record.get('id') == record_id:
                    data_size = len(json.dumps(record))
                    self._update_metrics('read', True, data_size, __import__('time').time() - start_time)
                    return record

            self._update_metrics('read', True, 0, __import__('time').time() - start_time)
            return None

        except Exception as e:
            self._update_metrics('read', False, 0, __import__('time').time() - start_time)
            self._logger.error(f"Error retrieving record {record_id} from {collection}: {e}")
            return None

    def query(self, collection: str, filters: Optional[List[QueryFilter]] = None,
             options: Optional[QueryOptions] = None) -> Iterator[Dict[str, Any]]:
        """Query records with optional filtering.

        Args:
            collection: Collection name
            filters: Query filters
            options: Query options

        Returns:
            Iterator over matching records
        """
        start_time = __import__('time').time()

        try:
            collection_data = self._load_collection(collection)
            results = self._apply_filters(collection_data, filters)

            # Apply sorting
            if options and options.sort_by:
                reverse = options.sort_order.lower() == 'desc'
                results.sort(key=lambda x: x.get(options.sort_by, 0), reverse=reverse)

            # Apply pagination
            if options and options.offset:
                results = results[options.offset:]
            if options and options.limit:
                results = results[:options.limit]

            # Apply field selection
            if options and options.fields:
                results = [{k: v for k, v in r.items() if k in options.fields} for r in results]

            data_size = sum(len(json.dumps(r)) for r in results)
            self._update_metrics('query', True, data_size, __import__('time').time() - start_time)

            return iter(results)

        except Exception as e:
            self._update_metrics('query', False, 0, __import__('time').time() - start_time)
            self._logger.error(f"Error querying {collection}: {e}")
            return iter([])

    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record by ID.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            True if record was deleted
        """
        start_time = __import__('time').time()

        try:
            collection_data = self._load_collection(collection)
            original_length = len(collection_data)

            # Filter out the record
            collection_data = [r for r in collection_data if r.get('id') != record_id]

            if len(collection_data) < original_length:
                # Save updated data
                self._save_collection(collection, collection_data)

                # Update cache
                self._data_cache[collection] = collection_data

                self._update_metrics('delete', True, 0, __import__('time').time() - start_time)
                return True
            else:
                self._update_metrics('delete', True, 0, __import__('time').time() - start_time)
                return False

        except Exception as e:
            self._update_metrics('delete', False, 0, __import__('time').time() - start_time)
            self._logger.error(f"Error deleting record {record_id} from {collection}: {e}")
            return False

    def create_collection(self, collection: str, schema: Optional[Dict[str, Any]] = None) -> None:
        """Create a new collection (no-op for file-based storage).

        Args:
            collection: Collection name
            schema: Optional schema (ignored)
        """
        # Ensure collection file exists
        collection_path = self._get_collection_path(collection)
        if not collection_path.exists():
            self._save_collection(collection, [])

    def drop_collection(self, collection: str) -> None:
        """Drop a collection by deleting its file.

        Args:
            collection: Collection name
        """
        try:
            collection_path = self._get_collection_path(collection)
            if collection_path.exists():
                os.remove(collection_path)

            # Remove from cache
            self._data_cache.pop(collection, None)

        except Exception as e:
            self._logger.error(f"Error dropping collection {collection}: {e}")
            raise

    def _extract_base_path(self, connection_string: str) -> str:
        """Extract base path from connection string.

        Args:
            connection_string: Connection string like 'json:///path/to/data'

