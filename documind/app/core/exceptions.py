"""Custom exceptions for DocuMind."""

from typing import Any, Dict, Optional


class DocuMindException(Exception):
    """Base exception for DocuMind."""

    def __init__(
        self,
        message: str,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DocuMindException):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details=details,
        )


class NotFoundError(DocuMindException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            error_code="not_found",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
        )


class AuthenticationError(DocuMindException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
        )


class AuthorizationError(DocuMindException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
        )


class CodeAnalysisError(DocuMindException):
    """Code analysis error."""

    def __init__(self, message: str, language: Optional[str] = None, file_path: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="code_analysis_error",
            status_code=422,
            details={"language": language, "file_path": file_path},
        )


class DocumentationError(DocuMindException):
    """Documentation generation error."""

    def __init__(self, message: str, component: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="documentation_error",
            status_code=422,
            details={"component": component},
        )


class IntegrationError(DocuMindException):
    """External service integration error."""

    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service}: {message}",
            error_code="integration_error",
            status_code=502,
            details={"service": service, **(details or {})},
        )


class RateLimitError(DocuMindException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", reset_time: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="rate_limit_error",
            status_code=429,
            details={"reset_time": reset_time},
        )
