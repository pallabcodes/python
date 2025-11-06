
        Args:
            backend_type: Type of backend

        Returns:
            Configuration template dictionary

        Raises:
            ValueError: If backend type is unsupported
        """
        backend_type = backend_type.lower()

        if backend_type == 'sqlite':
            return {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/analytics.db',
                'max_connections': 10,
                'connection_timeout': 30.0,
                'retry_count': 3,
                'retry_delay': 1.0,
                'enable_metrics': True,
                'enable_compression': False,
                'batch_size': 100,
                'flush_interval': 60,
                # SQLite-specific options
                'journal_mode': 'WAL',
                'synchronous_mode': 'NORMAL',
                'cache_size': -64000
            }
        elif backend_type == 'json':
            return {
                'backend_type': 'json',
                'connection_string': 'json:///data/json_storage',
                'max_connections': 10,
                'connection_timeout': 30.0,
                'retry_count': 3,
                'retry_delay': 1.0,
                'enable_metrics': True,
                'enable_compression': True,
                'batch_size': 100,
                'flush_interval': 60
            }
        elif backend_type == 'cache':
            return {
                'backend_type': 'cache',
                'connection_string': 'cache://memory',
                'max_connections': 10,
                'connection_timeout': 30.0,
                'retry_count': 3,
                'retry_delay': 1.0,
                'enable_metrics': True,
                'enable_compression': False,
                'batch_size': 100,
                'flush_interval': 60,
                # Cache-specific options
                'max_size': 10000,
                'default_ttl': None,
                'persistence_file': None,
                'auto_save_interval': 300
            }
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    @staticmethod
    def validate_config(config: StorageConfig) -> None:
        """Validate storage configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate common fields
        if not config.backend_type:
            raise ValueError("backend_type is required")

        if not config.connection_string:
            raise ValueError("connection_string is required")

        if config.max_connections < 1:
            raise ValueError("max_connections must be >= 1")

        if config.connection_timeout <= 0:
            raise ValueError("connection_timeout must be > 0")

        if config.retry_count < 0:
            raise ValueError("retry_count must be >= 0")

        if config.retry_delay <= 0:
            raise ValueError("retry_delay must be > 0")

        if config.batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        if config.flush_interval < 1:
            raise ValueError("flush_interval must be >= 1")

        # Backend-specific validation
        backend_type = config.backend_type.lower()

        if backend_type == 'sqlite':
            if not config.connection_string.startswith(('sqlite:///', '/')):
                raise ValueError("SQLite connection string must be absolute path or start with 'sqlite:///'")
        elif backend_type == 'json':
            if not config.connection_string.startswith(('json:///', '/')):
                raise ValueError("JSON connection string must be absolute path or start with 'json:///'")
        elif backend_type == 'cache':
            if not config.connection_string.startswith('cache://'):
                raise ValueError("Cache connection string must start with 'cache://'")
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
