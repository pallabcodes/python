        Args:
            message: Message to normalize

        Returns:
            Message with normalized timestamps
        """
        timestamp_fields = [
            'data.timestamp',
            'data.entry.published',
            'metadata.timestamp'
        ]

        for field_path in timestamp_fields:
            value = self._extract_field(message, field_path)
            if value is not None:
                normalized_ts = self._normalize_timestamp(value)
                if normalized_ts is not None:
                    self._set_field(message, field_path, normalized_ts)

        return message

    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate message against configured rules.

        Args:
            message: Message to validate

        Returns:
            True if message passes validation
        """
        for rule in self._validation_rules:
            try:
                field_path = rule.get('field')
                if not field_path:
                    continue

                value = self._extract_field(message, field_path)
                rule_type = rule.get('type', 'required')

                if rule_type == 'required' and value is None:
                    return False
                elif rule_type == 'type' and not isinstance(value, rule.get('expected_type')):
                    return False
                elif rule_type == 'range' and isinstance(value, (int, float)):
                    min_val = rule.get('min')
                    max_val = rule.get('max')
                    if min_val is not None and value < min_val:
                        return False
                    if max_val is not None and value > max_val:
                        return False

            except Exception as e:
                self._logger.warning(f"Error validating rule {rule}: {e}")
                return False

        return True

    def _convert_value(self, value: Any, target_type: str) -> Optional[Any]:
        """Convert a value to the target type.

        Args:
            value: Value to convert
            target_type: Target type string

        Returns:
            Converted value or None if conversion fails
        """
        try:
            if target_type == 'str':
                return str(value)
            elif target_type == 'int':
                return int(value)
            elif target_type == 'float':
                return float(value)
            elif target_type == 'bool':
                return bool(value)
            else:
                return value
        except (ValueError, TypeError):
            return None

    def _normalize_timestamp(self, timestamp: Any) -> Optional[float]:
        """Normalize timestamp to Unix timestamp format.

        Args:
            timestamp: Timestamp value to normalize

        Returns:
            Unix timestamp or None if normalization fails
        """
        try:
            if isinstance(timestamp, (int, float)):
                return float(timestamp)
            elif isinstance(timestamp, str):
                # Try common date formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(timestamp, fmt)
                        return dt.timestamp()
                    except ValueError:
                        continue
            elif isinstance(timestamp, datetime):
                return timestamp.timestamp()
        except Exception:
            pass

        return None

    def _format_date(self, date_str: Any, input_format: str, output_format: str) -> Optional[str]:
        """Format a date string.

        Args:
            date_str: Input date string
            input_format: Input date format
            output_format: Output date format

        Returns:
            Formatted date string or None
        """
        try:
            if isinstance(date_str, str):
                dt = datetime.strptime(date_str, input_format)
                return dt.strftime(output_format)
        except Exception:
            pass
        return None

    def _deep_copy_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of the message.

        Args:
            message: Message to copy

        Returns:
            Deep copy of the message
        """
        return json.loads(json.dumps(message, default=str))

    def _extract_field(self, message: Dict[str, Any], field_path: str) -> Any:
        """Extract a field value using dot notation.

        Args:
            message: Message to extract from
            field_path: Field path (e.g., 'data.entry.title')

        Returns:
            Field value or None
        """
        try:
            current = message
            for part in field_path.split('.'):
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current
        except Exception:
            return None

    def _set_field(self, message: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set a field value using dot notation.

        Args:
            message: Message to modify
            field_path: Field path (e.g., 'data.entry.title')
            value: Value to set
        """
        parts = field_path.split('.')
        current = message

        # Navigate to the parent object
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        # Set the value
        current[parts[-1]] = value
