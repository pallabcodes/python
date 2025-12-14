"""Custom exceptions for Acquisitor."""

from typing import Any, Dict, Optional


class AcquisitorException(Exception):
    """Base exception for Acquisitor application."""

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.headers = headers
        super().__init__(self.detail)


class ValidationError(AcquisitorException):
    """Validation error."""

    def __init__(self, detail: str, field: Optional[str] = None):
        error_code = f"VALIDATION_ERROR{'_' + field.upper() if field else ''}"
        super().__init__(detail, status_code=400, error_code=error_code)


class NotFoundError(AcquisitorException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f": {resource_id}"
        error_code = f"{resource.upper()}_NOT_FOUND"
        super().__init__(detail, status_code=404, error_code=error_code)


class AuthenticationError(AcquisitorException):
    """Authentication error."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail, status_code=401, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(AcquisitorException):
    """Authorization error."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail, status_code=403, error_code="AUTHORIZATION_ERROR")


class ExternalAPIError(AcquisitorException):
    """External API error."""

    def __init__(self, service: str, detail: str, status_code: int = 502):
        error_code = f"{service.upper()}_API_ERROR"
        super().__init__(detail, status_code=status_code, error_code=error_code)


class ResearchCollectionError(AcquisitorException):
    """Research data collection error."""

    def __init__(self, source: str, detail: str):
        error_code = f"COLLECTION_ERROR_{source.upper()}"
        super().__init__(detail, status_code=500, error_code=error_code)


class AnalysisError(AcquisitorException):
    """Data analysis error."""

    def __init__(self, operation: str, detail: str):
        error_code = f"ANALYSIS_ERROR_{operation.upper()}"
        super().__init__(detail, status_code=500, error_code=error_code)


class DatabaseError(AcquisitorException):
    """Database operation error."""

    def __init__(self, operation: str, detail: str):
        error_code = f"DATABASE_ERROR_{operation.upper()}"
        super().__init__(detail, status_code=500, error_code=error_code)


class ConfigurationError(AcquisitorException):
    """Configuration error."""

    def __init__(self, setting: str, detail: str):
        error_code = f"CONFIG_ERROR_{setting.upper()}"
        super().__init__(detail, status_code=500, error_code=error_code)
