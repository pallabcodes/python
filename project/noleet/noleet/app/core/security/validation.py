"""
Input validation and sanitization for security hardening.
OWASP compliant input validation and sanitization.
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from pydantic import BaseModel, validator, ValidationError
import logging

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Custom exception for security validation failures."""
    pass


class InputSanitizer:
    """Comprehensive input sanitization utilities."""

    # OWASP recommended patterns for dangerous content
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'vbscript:',                  # VBScript URLs
        r'on\w+\s*=',                  # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # Iframes
        r'<object[^>]*>.*?</object>',  # Object tags
        r'<embed[^>]*>.*?</embed>',    # Embed tags
        r'<form[^>]*>.*?</form>',      # Form tags
        r'<input[^>]*>',               # Input tags
        r'<meta[^>]*>',                # Meta tags
        r'<!--.*?-->',                 # HTML comments with scripts
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r';\s*(drop|delete|update|insert|alter|create|truncate)\s',
        r'union\s+select',
        r'--\s*$',
        r'#\s*$',
        r'/\*.*?\*/',
        r'xp_cmdshell',
        r'exec\s*\(',
        r'execute\s*\(',
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'..%2f',
        r'..%5c',
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r';\s*(rm|del|format|shutdown|reboot)',
        r'\|\s*(cat|ls|dir|type)',
        r'`.*?`',
        r'\$\(.*?\)',
        r'&&',
        r'\|\|',
    ]

    @staticmethod
    def sanitize_html(text: str, allowed_tags: Optional[List[str]] = None) -> str:
        """Sanitize HTML content using bleach."""
        if allowed_tags is None:
            allowed_tags = []  # No HTML allowed by default

        # Clean the text
        cleaned = bleach.clean(
            text,
            tags=allowed_tags,
            attributes={},
            protocols=['http', 'https'],  # Only allow safe protocols
            strip=True
        )

        return cleaned

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize plain text input."""
        if not isinstance(text, str):
            raise SecurityValidationError("Input must be a string")

        # Remove null bytes
        text = text.replace('\x00', '')

        # Escape HTML entities
        text = html.escape(text, quote=True)

        # Remove dangerous patterns
        for pattern in InputSanitizer.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Normalize whitespace
        text = ' '.join(text.split())

        return text.strip()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for secure file operations."""
        if not filename:
            raise SecurityValidationError("Filename cannot be empty")

        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)

        # Remove dangerous extensions
        dangerous_exts = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')

        if f'.{ext.lower()}' in dangerous_exts:
            filename = f"{name}.txt"  # Safe default extension

        return filename[:255]  # Limit length

    @staticmethod
    def validate_sql_safe(text: str) -> bool:
        """Check if text is safe from SQL injection."""
        if not isinstance(text, str):
            return False

        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return False

        return True

    @staticmethod
    def validate_path_safe(path: str) -> bool:
        """Check if path is safe from path traversal."""
        if not isinstance(path, str):
            return False

        for pattern in InputSanitizer.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected: {pattern}")
                return False

        return True

    @staticmethod
    def validate_command_safe(command: str) -> bool:
        """Check if command string is safe from command injection."""
        if not isinstance(command, str):
            return False

        for pattern in InputSanitizer.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(f"Command injection pattern detected: {pattern}")
                return False

        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format and security."""
        if not isinstance(email, str):
            return False

        # Basic email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return False

        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '|', '&', '`', '$', '(', ')']
        if any(char in email for char in dangerous_chars):
            return False

        return len(email) <= 254  # RFC 5321 limit

    @staticmethod
    def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """Validate URL format and security."""
        if not isinstance(url, str):
            return False

        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in allowed_schemes:
                return False

            # Check for dangerous characters in netloc
            if any(char in parsed.netloc for char in ['<', '>', '"', "'", ';']):
                return False

            return True
        except Exception:
            return False


class SecureBaseModel(BaseModel):
    """Base model with security validation."""

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = False

    @validator('*', pre=True, each_item=True)
    def sanitize_input(cls, v, field):
        """Automatically sanitize input for string fields."""
        if isinstance(v, str):
            # Skip sanitization for specific fields that need raw input
            skip_fields = getattr(cls.Config, 'skip_sanitization', [])
            if field.name not in skip_fields:
                return InputSanitizer.sanitize_text(v)
        return v


class UserInput(BaseModel):
    """Secure user input model."""
    text: str
    max_length: Optional[int] = 10000

    @validator('text')
    def validate_length(cls, v, values):
        max_len = values.get('max_length', 10000)
        if len(v) > max_len:
            raise SecurityValidationError(f"Input too long (max {max_len} characters)")
        return v

    @validator('text')
    def validate_content(cls, v):
        # Check for SQL injection
        if not InputSanitizer.validate_sql_safe(v):
            raise SecurityValidationError("Input contains potentially dangerous SQL patterns")

        # Check for command injection
        if not InputSanitizer.validate_command_safe(v):
            raise SecurityValidationError("Input contains potentially dangerous command patterns")

        return v


class FileUpload(BaseModel):
    """Secure file upload model."""
    filename: str
    content_type: str
    size: int
    max_size: Optional[int] = 10 * 1024 * 1024  # 10MB default

    @validator('filename')
    def validate_filename(cls, v):
        sanitized = InputSanitizer.sanitize_filename(v)
        if sanitized != v:
            raise SecurityValidationError("Filename contains invalid characters")
        return sanitized

    @validator('content_type')
    def validate_content_type(cls, v):
        # Allow only safe content types
        allowed_types = [
            'text/plain',
            'text/csv',
            'application/json',
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
        ]

        if v not in allowed_types:
            raise SecurityValidationError(f"Content type '{v}' not allowed")
        return v

    @validator('size')
    def validate_size(cls, v, values):
        max_size = values.get('max_size', 10 * 1024 * 1024)
        if v > max_size:
            raise SecurityValidationError(f"File too large (max {max_size} bytes)")
        return v


def secure_input_validator(func: Callable) -> Callable:
    """Decorator to validate and sanitize function inputs."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitize string arguments
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(InputSanitizer.sanitize_text(arg))
            else:
                sanitized_args.append(arg)

        # Sanitize string keyword arguments
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = InputSanitizer.sanitize_text(value)
            else:
                sanitized_kwargs[key] = value

        # Validate for security issues
        for arg in sanitized_args:
            if isinstance(arg, str):
                if not InputSanitizer.validate_sql_safe(arg):
                    raise SecurityValidationError("SQL injection pattern detected in arguments")
                if not InputSanitizer.validate_command_safe(arg):
                    raise SecurityValidationError("Command injection pattern detected in arguments")

        return func(*sanitized_args, **sanitized_kwargs)
    return wrapper


def rate_limit(max_calls: int, time_window: int):
    """Rate limiting decorator."""
    from functools import wraps
    import time
    from collections import defaultdict

    calls = defaultdict(list)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simple in-memory rate limiting (use Redis in production)
            current_time = time.time()
            client_key = "default"  # In production, use user ID or IP

            # Clean old calls
            calls[client_key] = [
                call_time for call_time in calls[client_key]
                if current_time - call_time < time_window
            ]

            if len(calls[client_key]) >= max_calls:
                raise SecurityValidationError(
                    f"Rate limit exceeded. Max {max_calls} calls per {time_window} seconds"
                )

            calls[client_key].append(current_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityAudit:
    """Security auditing and logging."""

    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log security-related events."""
        log_data = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": None,  # Will be set by logging formatter
            "details": details
        }

        if severity == "CRITICAL":
            logger.critical(f"Security Event: {event_type}", extra=log_data)
        elif severity == "ERROR":
            logger.error(f"Security Event: {event_type}", extra=log_data)
        elif severity == "WARNING":
            logger.warning(f"Security Event: {event_type}", extra=log_data)
        else:
            logger.info(f"Security Event: {event_type}", extra=log_data)

    @staticmethod
    def log_failed_validation(validation_type: str, input_data: Any, error: str):
        """Log validation failures."""
        SecurityAudit.log_security_event(
            "VALIDATION_FAILED",
            {
                "validation_type": validation_type,
                "input_data": str(input_data)[:100],  # Truncate for security
                "error": error
            },
            "WARNING"
        )

    @staticmethod
    def log_suspicious_activity(activity_type: str, details: Dict[str, Any]):
        """Log suspicious activities."""
        SecurityAudit.log_security_event(
            "SUSPICIOUS_ACTIVITY",
            {"activity_type": activity_type, **details},
            "WARNING"
        )
