"""
Unit tests for security validation functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from noleet.app.core.security.validation import (
    InputSanitizer,
    SecurityValidationError,
    UserInput,
    FileUpload,
    secure_input_validator,
    SecurityAudit
)


class TestInputSanitizer:
    """Test input sanitization functionality."""

    def test_sanitize_text_basic(self):
        """Test basic text sanitization."""
        text = "<script>alert('xss')</script>Hello World"
        sanitized = InputSanitizer.sanitize_text(text)

        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert "Hello World" in sanitized

    def test_sanitize_text_null_bytes(self):
        """Test null byte removal."""
        text = "Hello\x00World\x00"
        sanitized = InputSanitizer.sanitize_text(text)

        assert "\x00" not in sanitized
        assert sanitized == "HelloWorld"

    def test_sanitize_html_allowed_tags(self):
        """Test HTML sanitization with allowed tags."""
        html = "<p>Hello <strong>world</strong></p><script>evil()</script>"
        sanitized = InputSanitizer.sanitize_html(html, allowed_tags=['p', 'strong'])

        assert "<script>" not in sanitized
        assert "<p>Hello <strong>world</strong></p>" == sanitized

    def test_sanitize_filename_dangerous(self):
        """Test dangerous filename sanitization."""
        dangerous_names = [
            "../../../etc/passwd",
            "file.exe",
            "script.bat",
            "file<name>.txt"
        ]

        for name in dangerous_names:
            sanitized = InputSanitizer.sanitize_filename(name)
            # Should not contain dangerous patterns
            assert ".." not in sanitized
            assert ".exe" not in sanitized
            assert ".bat" not in sanitized
            assert "<" not in sanitized

    def test_validate_sql_safe(self):
        """Test SQL injection detection."""
        safe_queries = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT name FROM users WHERE name = 'john'",
            "SELECT * FROM users WHERE age > 18"
        ]

        for query in safe_queries:
            assert InputSanitizer.validate_sql_safe(query)

        dangerous_queries = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin",
            "SELECT * FROM users -- DROP TABLE users"
        ]

        for query in dangerous_queries:
            assert not InputSanitizer.validate_sql_safe(query)

    def test_validate_path_safe(self):
        """Test path traversal detection."""
        safe_paths = [
            "/app/data/file.txt",
            "data/file.txt",
            "file.txt"
        ]

        for path in safe_paths:
            assert InputSanitizer.validate_path_safe(path)

        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\cmd.exe",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for path in dangerous_paths:
            assert not InputSanitizer.validate_path_safe(path)

    def test_validate_email(self):
        """Test email validation."""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user_name@subdomain.example.org"
        ]

        for email in valid_emails:
            assert InputSanitizer.validate_email(email)

        invalid_emails = [
            "invalid-email",
            "user@",
            "@domain.com",
            "user@domain..com",
            "user@domain<script>.com"
        ]

        for email in invalid_emails:
            assert not InputSanitizer.validate_email(email)

    def test_validate_url(self):
        """Test URL validation."""
        valid_urls = [
            "https://example.com",
            "http://subdomain.example.com/path?param=value",
            "https://example.com:8080/path"
        ]

        for url in valid_urls:
            assert InputSanitizer.validate_url(url)

        invalid_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "ftp://example.com"
        ]

        for url in invalid_urls:
            assert not InputSanitizer.validate_url(url, allowed_schemes=['http', 'https'])


class TestUserInput:
    """Test UserInput model validation."""

    def test_valid_user_input(self):
        """Test valid user input."""
        input_data = UserInput(text="Hello World", max_length=100)
        assert input_data.text == "Hello World"
        assert input_data.max_length == 100

    def test_user_input_sanitization(self):
        """Test automatic input sanitization."""
        dangerous_input = UserInput(text="<script>alert('xss')</script>Hello")
        assert "<script>" not in dangerous_input.text
        assert "Hello" in dangerous_input.text

    def test_user_input_length_validation(self):
        """Test input length validation."""
        with pytest.raises(SecurityValidationError):
            UserInput(text="A" * 10001)  # Exceeds default max length

    def test_user_input_sql_injection(self):
        """Test SQL injection detection in user input."""
        with pytest.raises(SecurityValidationError):
            UserInput(text="SELECT * FROM users; DROP TABLE users;")


class TestFileUpload:
    """Test FileUpload model validation."""

    def test_valid_file_upload(self):
        """Test valid file upload."""
        upload = FileUpload(
            filename="test.txt",
            content_type="text/plain",
            size=1024
        )
        assert upload.filename == "test.txt"
        assert upload.content_type == "text/plain"
        assert upload.size == 1024

    def test_file_upload_dangerous_filename(self):
        """Test dangerous filename sanitization."""
        with pytest.raises(SecurityValidationError):
            FileUpload(
                filename="../../../etc/passwd",
                content_type="text/plain",
                size=1024
            )

    def test_file_upload_invalid_content_type(self):
        """Test invalid content type rejection."""
        with pytest.raises(SecurityValidationError):
            FileUpload(
                filename="test.exe",
                content_type="application/x-executable",
                size=1024
            )

    def test_file_upload_size_limit(self):
        """Test file size limit enforcement."""
        with pytest.raises(SecurityValidationError):
            FileUpload(
                filename="large_file.txt",
                content_type="text/plain",
                size=20 * 1024 * 1024  # 20MB, exceeds default 10MB
            )


class TestSecureInputValidator:
    """Test secure input validator decorator."""

    def test_secure_validator_sanitization(self):
        """Test that decorator sanitizes inputs."""
        @secure_input_validator
        def test_function(text: str) -> str:
            return text

        result = test_function("<script>evil</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result

    def test_secure_validator_sql_injection(self):
        """Test SQL injection detection in decorated functions."""
        @secure_input_validator
        def test_function(query: str) -> str:
            return query

        with pytest.raises(SecurityValidationError):
            test_function("SELECT * FROM users; DROP TABLE users;")


class TestSecurityAudit:
    """Test security auditing functionality."""

    @patch('noleet.app.core.security.validation.logger')
    def test_audit_log_security_event(self, mock_logger):
        """Test security event logging."""
        SecurityAudit.log_security_event(
            "TEST_EVENT",
            {"test": "data"},
            "WARNING"
        )

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "Security Event: TEST_EVENT" in call_args[0][0]
        assert call_args[1]["extra"]["event_type"] == "TEST_EVENT"

    def test_audit_log_failed_validation(self, mock_logger):
        """Test validation failure logging."""
        with patch('noleet.app.core.security.validation.logger') as mock_logger:
            SecurityAudit.log_failed_validation(
                "email_validation",
                "invalid@email",
                "Invalid format"
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "VALIDATION_FAILED" in call_args[0][0]

    def test_audit_log_suspicious_activity(self, mock_logger):
        """Test suspicious activity logging."""
        with patch('noleet.app.core.security.validation.logger') as mock_logger:
            SecurityAudit.log_suspicious_activity(
                "unusual_login",
                {"ip": "192.168.1.1", "attempts": 5}
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "SUSPICIOUS_ACTIVITY" in call_args[0][0]


class TestRateLimitDecorator:
    """Test rate limiting decorator from validation module."""

    def test_rate_limit_decorator(self):
        """Test rate limit decorator functionality."""
        from noleet.app.core.security.validation import rate_limit

        call_count = 0

        @rate_limit(max_calls=2, time_window=1)
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        # First two calls should succeed
        assert test_function() == "success"
        assert test_function() == "success"
        assert call_count == 2

        # Third call should fail
        with pytest.raises(SecurityValidationError, match="Rate limit exceeded"):
            test_function()

        assert call_count == 2  # Should not increment on failure
