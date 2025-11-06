        """
        start_time = time.time()

        with self._cache_lock:
            if record_id in self._cache[collection]:
                del self._cache[collection][record_id]

                # Remove from LRU queue
                self._lru_queues[collection] = deque(
                    (rid for rid in self._lru_queues[collection] if rid != record_id),
                    maxlen=self._max_size
                )

                self._update_metrics('delete', True, 0, time.time() - start_time)
                return True

        self._update_metrics('delete', True, 0, time.time() - start_time)
        return False

    def create_collection(self, collection: str, schema: Optional[Dict[str, Any]] = None) -> None:
        """Create a new collection (no-op for cache).

        Args:
            collection: Collection name
            schema: Optional schema (ignored)
        """
        # Ensure collection exists in cache
        with self._cache_lock:
            if collection not in self._cache:
                self._cache[collection] = {}

    def drop_collection(self, collection: str) -> None:
        """Drop a collection from cache.

        Args:
            collection: Collection name
        """
        with self._cache_lock:
            self._cache.pop(collection, None)
            self._lru_queues.pop(collection, None)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics.

        Returns:
            Cache statistics dictionary
        """
        with self._cache_lock:
            stats = {
                'total_collections': len(self._cache),
                'total_entries': sum(len(entries) for entries in self._cache.values()),
                'collections': {}
            }

            for collection, entries in self._cache.items():
                valid_entries = [e for e in entries.values() if not e.is_expired()]
                expired_count = len(entries) - len(valid_entries)

                stats['collections'][collection] = {
                    'total_entries': len(entries),
                    'valid_entries': len(valid_entries),
                    'expired_entries': expired_count,
                    'lru_queue_size': len(self._lru_queues[collection])
                }

            return stats

    def clear_expired(self) -> int:
        """Clear expired entries from cache.

        Returns:
            Number of entries cleared
        """
        cleared = 0

        with self._cache_lock:
            for collection in list(self._cache.keys()):
                expired_ids = []

                for record_id, entry in self._cache[collection].items():
                    if entry.is_expired():
                        expired_ids.append(record_id)

                for record_id in expired_ids:
                    del self._cache[collection][record_id]
                    cleared += 1

                # Update LRU queue
                if expired_ids:
                    self._lru_queues[collection] = deque(
                        (rid for rid in self._lru_queues[collection] if rid not in expired_ids),
                        maxlen=self._max_size
                    )

        return cleared

    def _update_lru(self, collection: str, record_id: str) -> None:
        """Update LRU queue for a record.

        Args:
            collection: Collection name
            record_id: Record ID
        """
        queue = self._lru_queues[collection]

        # Remove if already in queue
        try:
            queue.remove(record_id)
        except ValueError:
            pass

        # Add to end (most recently used)
        queue.append(record_id)

    def _enforce_size_limit(self, collection: str) -> None:
        """Enforce size limits using LRU eviction.

        Args:
            collection: Collection name
        """
        cache = self._cache[collection]
        queue = self._lru_queues[collection]

        while len(cache) > self._max_size and queue:
            # Remove least recently used
            lru_id = queue.popleft()
            if lru_id in cache:
                del cache[lru_id]

    def _matches_filters(self, data: Dict[str, Any], filters: List[QueryFilter]) -> bool:
        """Check if data matches all filters.

        Args:
            data: Data to check
            filters: List of filters

        Returns:
            True if data matches all filters
        """
        for filter_obj in filters:
            if not self._matches_filter(data, filter_obj):
                return False
        return True

    def _matches_filter(self, data: Dict[str, Any], filter_obj: QueryFilter) -> bool:
        """Check if data matches a single filter.

        Args:
            data: Data to check
            filter_obj: Filter to match
