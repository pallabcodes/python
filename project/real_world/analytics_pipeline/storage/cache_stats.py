
        Returns:
            True if data matches filter
        """
        value = self._get_nested_value(data, filter_obj.field)
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
        else:
            return True

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value using dot notation.

        Args:
            data: Data dictionary
            field_path: Field path

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

    def _load_from_disk(self) -> None:
        """Load cache data from disk."""
        if not self._persistence_file or not os.path.exists(self._persistence_file):
            return

        try:
            with open(self._persistence_file, 'rb') as f:
                persisted_data = pickle.load(f)

            with self._cache_lock:
                self._cache = persisted_data.get('cache', defaultdict(dict))
                self._lru_queues = persisted_data.get('lru_queues', defaultdict(deque))

            self._logger.info(f"Loaded cache data from {self._persistence_file}")

        except Exception as e:
            self._logger.warning(f"Error loading cache from disk: {e}")

    def _save_to_disk(self) -> None:
        """Save cache data to disk."""
        if not self._persistence_file:
            return

        try:
            os.makedirs(os.path.dirname(self._persistence_file), exist_ok=True)

            with self._cache_lock:
                data_to_save = {
                    'cache': dict(self._cache),
                    'lru_queues': dict(self._lru_queues),
                    'saved_at': time.time()
                }

            with open(self._persistence_file, 'wb') as f:
                pickle.dump(data_to_save, f)

            self._logger.debug(f"Saved cache data to {self._persistence_file}")

        except Exception as e:
            self._logger.error(f"Error saving cache to disk: {e}")

    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        import threading

        def cleanup_worker():
            while self._connected:
                try:
                    time.sleep(60)  # Clean every minute
                    if self._connected:
                        cleared = self.clear_expired()
                        if cleared > 0:
                            self._logger.debug(f"Cleared {cleared} expired cache entries")
                except Exception as e:
                    self._logger.error(f"Error in cache cleanup: {e}")

        cleanup_thread = threading.Thread(
            target=cleanup_worker,
            name="CacheCleanup",
            daemon=True
        )
        cleanup_thread.start()

    def _create_connection(self) -> Any:
        """Create a connection (no-op for cache)."""
        return None

    def _close_connection(self, connection: Any) -> None:
        """Close a connection (no-op for cache)."""
        pass
