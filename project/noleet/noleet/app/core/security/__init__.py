"""
Security hardening module for NoLeet.
OWASP compliant security implementation.
"""

from .validation import (
    InputSanitizer,
    SecureBaseModel,
    UserInput,
    FileUpload,
    SecurityValidationError,
    secure_input_validator,
    SecurityAudit,
    rate_limit as validation_rate_limit
)

from .auth import (
    AuthManager,
    RBACManager,
    User,
    UserRole,
    Permission,
    JWTToken,
    LoginRequest,
    RegisterRequest,
    SecurityHeaders,
    PasswordPolicy,
    SessionManager,
    require_auth,
    require_role
)

from .rate_limiting import (
    RateLimiter,
    APIRateLimiter,
    DDoSProtection,
    CircuitBreaker,
    RateLimitViolation,
    rate_limit,
    rate_limiter,
    ddos_protection
)

from .validation import SecurityAudit as Audit

# Global security instances
auth_manager = AuthManager()
rbac_manager = RBACManager()
session_manager = SessionManager()

__all__ = [
    # Validation
    'InputSanitizer',
    'SecureBaseModel',
    'UserInput',
    'FileUpload',
    'SecurityValidationError',
    'secure_input_validator',
    'SecurityAudit',
    'validation_rate_limit',

    # Authentication & Authorization
    'AuthManager',
    'RBACManager',
    'User',
    'UserRole',
    'Permission',
    'JWTToken',
    'LoginRequest',
    'RegisterRequest',
    'SecurityHeaders',
    'PasswordPolicy',
    'SessionManager',
    'require_auth',
    'require_role',
    'auth_manager',
    'rbac_manager',
    'session_manager',

    # Rate Limiting & DDoS
    'RateLimiter',
    'APIRateLimiter',
    'DDoSProtection',
    'CircuitBreaker',
    'RateLimitViolation',
    'rate_limit',
    'rate_limiter',
    'ddos_protection',

    # Audit
    'Audit'
]
