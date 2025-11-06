
        if transform_type == 'lowercase':
            return lambda x: str(x).lower() if x else x
        elif transform_type == 'uppercase':
            return lambda x: str(x).upper() if x else x
        elif transform_type == 'strip':
            return lambda x: str(x).strip() if x else x
        elif transform_type == 'regex_replace':
            pattern = rule_config.get('pattern', '')
            replacement = rule_config.get('replacement', '')
            return lambda x: re.sub(pattern, replacement, str(x)) if x else x
        elif transform_type == 'date_format':
            input_format = rule_config.get('input_format', '%Y-%m-%d')
            output_format = rule_config.get('output_format', '%Y-%m-%d')
            return lambda x: self._format_date(x, input_format, output_format)
        elif transform_type == 'copy':
            return lambda x: x
        else:
            self._logger.warning(f"Unknown transform type: {transform_type}")
            return lambda x: x

    def _create_condition_function(self, condition_config: Optional[Dict[str, Any]]) -> Optional[Callable]:
        """Create a condition function from rule configuration.

        Args:
            condition_config: Condition configuration dictionary

        Returns:
            Condition function or None
        """
        if not condition_config:
            return None

        field = condition_config.get('field')
        operator = condition_config.get('operator', 'exists')
        value = condition_config.get('value')

        if operator == 'exists':
            return lambda msg: self._extract_field(msg, field) is not None
        elif operator == 'equals':
            return lambda msg: self._extract_field(msg, field) == value
        elif operator == 'contains':
            return lambda msg: value in str(self._extract_field(msg, field) or '')

        return None

    def _process_message(self, message: Any) -> Optional[Any]:
        """Process and transform a message.

        Args:
            message: Input message to transform

        Returns:
            Transformed message
        """
        if not isinstance(message, dict) or 'data' not in message:
            self._logger.warning("Invalid message format for transformation")
            return message

        # Create transformed copy
        transformed_message = self._deep_copy_message(message)

        try:
            # Apply field mappings
            transformed_message = self._apply_field_mappings(transformed_message)

            # Apply type conversions
            transformed_message = self._apply_type_conversions(transformed_message)

            # Apply custom transformation rules
            for rule in self._transformation_rules:
                if rule.condition is None or rule.condition(transformed_message):
                    self._apply_transformation_rule(transformed_message, rule)

            # Apply standard transformations
            if self._sanitize_text:
                transformed_message = self._sanitize_text_fields(transformed_message)

            if self._normalize_timestamps:
                transformed_message = self._normalize_timestamp_fields(transformed_message)

            # Validate the transformed message
            if not self._validate_message(transformed_message):
                self._logger.warning("Message failed validation after transformation")
                return None

            return transformed_message

        except Exception as e:
            self._logger.error(f"Error transforming message: {e}")
            return None

    def _apply_field_mappings(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mappings to rename or restructure fields.

        Args:
            message: Message to transform

        Returns:
            Message with field mappings applied
        """
        data = message.get('data', {})

        for source_path, target_path in self._field_mappings.items():
            value = self._extract_field(message, source_path)
            if value is not None:
                self._set_field(message, target_path, value)

        return message

    def _apply_type_conversions(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Apply type conversions to message fields.

        Args:
            message: Message to transform

        Returns:
            Message with type conversions applied
        """
        data = message.get('data', {})

        for field_path, target_type in self._type_conversions.items():
            value = self._extract_field(message, field_path)
            if value is not None:
                converted_value = self._convert_value(value, target_type)
                if converted_value is not None:
                    self._set_field(message, field_path, converted_value)

        return message

    def _apply_transformation_rule(self, message: Dict[str, Any], rule: TransformationRule) -> None:
        """Apply a single transformation rule.

        Args:
            message: Message to transform
            rule: Transformation rule to apply
        """
        value = self._extract_field(message, rule.field_path)

        if value is None:
            if rule.required and rule.default_value is not None:
                self._set_field(message, rule.field_path, rule.default_value)
            return

        try:
            transformed_value = rule.transform_function(value)
            self._set_field(message, rule.field_path, transformed_value)
        except Exception as e:
            self._logger.warning(f"Error applying transformation rule to {rule.field_path}: {e}")

    def _sanitize_text_fields(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize text fields to remove potentially harmful content.

        Args:
            message: Message to sanitize

        Returns:
            Message with sanitized text fields
        """
        # Define text fields that should be sanitized
        text_fields = [
            'data.entry.title',
            'data.entry.summary',
            'data.entry.content',
            'data.content'
        ]

        for field_path in text_fields:
            value = self._extract_field(message, field_path)
            if isinstance(value, str):
                # Basic sanitization: remove excessive whitespace and control characters
                sanitized = re.sub(r'\s+', ' ', value.strip())
                sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
                self._set_field(message, field_path, sanitized)

        return message

    def _normalize_timestamp_fields(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize timestamp fields to consistent format.

