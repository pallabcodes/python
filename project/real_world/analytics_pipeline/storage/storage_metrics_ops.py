            self._metrics.last_operation_time = time.time()

            if success:
                self._metrics.operations_successful += 1
                if operation in ('write', 'store'):
                    self._metrics.bytes_written += data_size
                elif operation in ('read', 'retrieve', 'query'):
                    self._metrics.bytes_read += data_size
            else:
                self._metrics.operations_failed += 1

            if duration is not None:
                # Update rolling average
                current_avg = self._metrics.average_operation_time
                total_ops = self._metrics.operations_total
                self._metrics.average_operation_time = (
                    (current_avg * (total_ops - 1)) + duration
                ) / total_ops

    def _calculate_average_operation_time(self) -> float:
        """Calculate average operation time.

        Returns:
            Average operation time in seconds
        """
        if self._metrics.operations_total == 0:
            return 0.0

        # Use stored average if available
        if hasattr(self._metrics, 'average_operation_time'):
            return self._metrics.average_operation_time

        return 0.0

    def _get_connection(self) -> Any:
        """Get a connection from the pool.

        Returns:
            Database connection
        """
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._metrics.active_connections += 1
                return conn
            else:
                # Create new connection if pool is empty
                return self._create_connection()

    def _return_connection(self, connection: Any) -> None:
        """Return a connection to the pool.

        Args:
            connection: Connection to return
        """
        with self._pool_lock:
            if len(self._connection_pool) < self._config.max_connections:
                self._connection_pool.append(connection)
            else:
                # Pool is full, close connection
                self._close_connection(connection)
            self._metrics.active_connections -= 1

    @abstractmethod
    def _create_connection(self) -> Any:
        """Create a new connection.

        Returns:
            New database connection
        """
        pass

    @abstractmethod
    def _close_connection(self, connection: Any) -> None:
        """Close a connection.

        Args:
            connection: Connection to close
        """
        pass

    def __enter__(self) -> 'StorageBackend':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self._shutdown_event.set()
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5.0)
        self.flush_batch()  # Final flush
        self.disconnect()
