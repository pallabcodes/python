            self._logger.error(f"Error storing record in cache {collection}: {e}")
            raise

    def store_batch(self, collection: str, data_list: List[Dict[str, Any]]) -> List[str]:
        """Store multiple records in batch.

        Args:
            collection: Collection name
            data_list: List of data records

        Returns:
            List of record IDs
        """
        start_time = time.time()
        record_ids = []

        try:
            with self._cache_lock:
                for data in data_list:
                    record_id = data.get('id') or str(__import__('uuid').uuid4())

                    # Prepare data
                    data_copy = data.copy()
                    data_copy['id'] = record_id

                    # Create cache entry
                    ttl = data_copy.pop('_ttl', self._default_ttl)
                    entry = CacheEntry(data_copy, ttl)

                    # Store in cache
                    self._cache[collection][record_id] = entry

                    # Update LRU queue
                    self._update_lru(collection, record_id)

                    record_ids.append(record_id)

                # Enforce size limits
                self._enforce_size_limit(collection)

            data_size = sum(len(pickle.dumps(data)) for data in data_list)
            self._update_metrics('write', True, data_size, time.time() - start_time)

            return record_ids

        except Exception as e:
            self._update_metrics('write', False, 0, time.time() - start_time)
            self._logger.error(f"Error in batch store to cache {collection}: {e}")
            raise

    def retrieve(self, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record from cache.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            Retrieved data or None
        """
        start_time = time.time()

        with self._cache_lock:
            entry = self._cache[collection].get(record_id)

            if entry and not entry.is_expired():
                entry.touch()
                self._update_lru(collection, record_id)

                data_size = len(pickle.dumps(entry.data))
                self._update_metrics('read', True, data_size, time.time() - start_time)

                return entry.data.copy()
            else:
                # Remove expired entry
                if entry:
                    del self._cache[collection][record_id]
                    self._lru_queues[collection] = deque(
                        (rid for rid in self._lru_queues[collection] if rid != record_id),
                        maxlen=self._max_size
                    )

                self._update_metrics('read', True, 0, time.time() - start_time)
                return None

    def query(self, collection: str, filters: Optional[List[QueryFilter]] = None,
             options: Optional[QueryOptions] = None) -> Iterator[Dict[str, Any]]:
        """Query records from cache.

        Args:
            collection: Collection name
            filters: Query filters
            options: Query options

        Returns:
            Iterator over matching records
        """
        start_time = time.time()

        try:
            with self._cache_lock:
                # Get all valid entries
                valid_entries = []
                for record_id, entry in self._cache[collection].items():
                    if not entry.is_expired():
                        entry.touch()
                        valid_entries.append((record_id, entry.data.copy()))

            # Apply filters
            if filters:
                valid_entries = [(rid, data) for rid, data in valid_entries
                               if self._matches_filters(data, filters)]

            # Sort results
            if options and options.sort_by:
                reverse = options.sort_order.lower() == 'desc'
                valid_entries.sort(key=lambda x: x[1].get(options.sort_by, 0), reverse=reverse)

            # Apply pagination
            if options and options.offset:
                valid_entries = valid_entries[options.offset:]
            if options and options.limit:
                valid_entries = valid_entries[:options.limit]

            # Extract data
            results = [data for _, data in valid_entries]

            # Apply field selection
            if options and options.fields:
                results = [{k: v for k, v in r.items() if k in options.fields} for r in results]

            data_size = sum(len(pickle.dumps(r)) for r in results)
            self._update_metrics('query', True, data_size, time.time() - start_time)

            return iter(results)

        except Exception as e:
            self._update_metrics('query', False, 0, time.time() - start_time)
            self._logger.error(f"Error querying cache {collection}: {e}")
            return iter([])

    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record from cache.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            True if record was deleted
