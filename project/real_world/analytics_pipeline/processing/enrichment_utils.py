def _add_timestamp_enrichment(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp enrichment to message.

        Args:
            message: Message to enrich

        Returns:
            Message with timestamp enrichment
        """
        current_time = time.time()
        message.setdefault('metadata', {})['enrichment_timestamp'] = current_time
        message['metadata']['pipeline_stage_timestamp'] = current_time
        return message

def _add_hash_enrichment(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Add message hash for deduplication.

    Args:
        message: Message to enrich

    Returns:
        Message with hash enrichment
    """
    # Create hash from key message content
    content_to_hash = {
        'source_type': message.get('data', {}).get('source_type'),
        'timestamp': message.get('data', {}).get('timestamp'),
        'content': str(message.get('data', {}).get('entry', {}))
    }

    # Create deterministic hash
    hash_input = json.dumps(content_to_hash, sort_keys=True, default=str)
    message_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    message.setdefault('metadata', {})['message_hash'] = message_hash
    return message


def _add_processing_enrichment(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Add processing metadata.

    Args:
        message: Message to enrich

    Returns:
        Message with processing metadata
    """
    metadata = message.setdefault('metadata', {})
    metadata['enriched_by'] = self.name
    metadata['enrichment_stage'] = self.__class__.__name__
    metadata['processing_pipeline'] = 'analytics_pipeline_v1'
    return message


def _deep_copy_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Create a deep copy of the message.

    Args:
        message: Message to copy

    Returns:
        Deep copy of the message
    """
    # Simple deep copy for JSON-serializable data
    return json.loads(json.dumps(message, default=str))


def _extract_field(self, message: Dict[str, Any], field_path: str) -> Any:
    """Extract a field value from message using dot notation.

    Args:
        message: Message to extract from
        field_path: Field path (e.g., 'data.entry.title')

    Returns:
        Field value or None if not found
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
