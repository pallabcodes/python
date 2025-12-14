"""
Authentication and authorization system with JWT and RBAC.
OWASP compliant authentication implementation.
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from functools import wraps
from dataclasses import dataclass

from pydantic import BaseModel, EmailStr, validator
import logging

from .validation import SecurityValidationError, InputSanitizer, SecurityAudit

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role enumeration."""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SYSTEM = "system"


class Permission(Enum):
    """System permissions."""
    # Basic permissions
    READ_PUBLIC = "read:public"
    READ_OWN = "read:own"

    # Project permissions
    CREATE_PROJECT = "create:project"
    READ_PROJECT = "read:project"
    UPDATE_PROJECT = "update:project"
    DELETE_PROJECT = "delete:project"

    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_SYSTEM = "manage:system"
    VIEW_ANALYTICS = "view:analytics"

    # API permissions
    USE_API = "use:api"
    HIGH_RATE_LIMIT = "high:rate_limit"


class User(BaseModel):
    """User model with security validation."""
    id: str
    email: EmailStr
    username: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    def __init__(self, **data):
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)

    @validator('username')
    def validate_username(cls, v):
        if not isinstance(v, str) or len(v) < 3:
            raise SecurityValidationError("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise SecurityValidationError("Username contains invalid characters")
        return v

    @validator('email')
    def validate_email(cls, v):
        if not InputSanitizer.validate_email(str(v)):
            raise SecurityValidationError("Invalid email format")
        return v


class JWTToken(BaseModel):
    """JWT token model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request model."""
    identifier: str  # username or email
    password: str

    @validator('identifier')
    def validate_identifier(cls, v):
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise SecurityValidationError("Identifier is required")
        return InputSanitizer.sanitize_text(v)

    @validator('password')
    def validate_password(cls, v):
        if not isinstance(v, str) or len(v) < 8:
            raise SecurityValidationError("Password must be at least 8 characters")
        return v  # Don't sanitize passwords


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str
    confirm_password: str

    @validator('email')
    def validate_email(cls, v):
        if not InputSanitizer.validate_email(str(v)):
            raise SecurityValidationError("Invalid email format")
        return v

    @validator('username')
    def validate_username(cls, v):
        if not isinstance(v, str) or len(v) < 3:
            raise SecurityValidationError("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise SecurityValidationError("Username contains invalid characters")
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise SecurityValidationError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise SecurityValidationError("Password must contain uppercase letter")
        if not re.search(r'[a-z]', v):
            raise SecurityValidationError("Password must contain lowercase letter")
        if not re.search(r'\d', v):
            raise SecurityValidationError("Password must contain digit")
        return v

    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'password' in values and v != values['password']:
            raise SecurityValidationError("Passwords do not match")
        return v


class AuthManager:
    """Authentication and authorization manager."""

    def __init__(self,
                 secret_key: Optional[str] = None,
                 jwt_algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

        # In production, use Redis or database
        self._users: Dict[str, User] = {}
        self._password_hashes: Dict[str, str] = {}

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False

    def create_user(self, register_request: RegisterRequest) -> User:
        """Create new user."""
        # Check if user already exists
        for user in self._users.values():
            if user.email == register_request.email or user.username == register_request.username:
                raise SecurityValidationError("User already exists")

        # Create user
        user_id = secrets.token_hex(16)
        hashed_password = self.hash_password(register_request.password)

        user = User(
            id=user_id,
            email=register_request.email,
            username=register_request.username,
            role=UserRole.USER
        )

        self._users[user_id] = user
        self._password_hashes[user_id] = hashed_password

        SecurityAudit.log_security_event("USER_CREATED", {"user_id": user_id, "username": user.username})
        return user

    def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate user with identifier and password."""
        # Find user by email or username
        user = None
        for u in self._users.values():
            if u.email == identifier or u.username == identifier:
                user = u
                break

        if not user:
            SecurityAudit.log_security_event("LOGIN_FAILED", {"identifier": identifier, "reason": "user_not_found"}, "WARNING")
            return None

        # Check if account is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            SecurityAudit.log_security_event("LOGIN_FAILED", {"user_id": user.id, "reason": "account_locked"}, "WARNING")
            raise SecurityValidationError("Account is temporarily locked")

        # Verify password
        hashed_password = self._password_hashes.get(user.id)
        if not hashed_password or not self.verify_password(password, hashed_password):
            user.failed_login_attempts += 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                SecurityAudit.log_security_event("ACCOUNT_LOCKED", {"user_id": user.id}, "WARNING")

            SecurityAudit.log_security_event("LOGIN_FAILED", {"user_id": user.id, "reason": "invalid_password"}, "WARNING")
            return None

        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        SecurityAudit.log_security_event("LOGIN_SUCCESS", {"user_id": user.id, "username": user.username})
        return user

    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": "noleet",
            "aud": "noleet-users"
        }

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.jwt_algorithm)
        return token

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.jwt_algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            SecurityAudit.log_security_event("TOKEN_EXPIRED", {}, "INFO")
            return None
        except jwt.InvalidTokenError:
            SecurityAudit.log_security_event("TOKEN_INVALID", {}, "WARNING")
            return None

    def get_current_user(self, token: str) -> Optional[User]:
        """Get user from JWT token."""
        payload = self.verify_token(token)
        if not payload or "sub" not in payload:
            return None

        user_id = payload["sub"]
        return self._users.get(user_id)

    def refresh_access_token(self, refresh_token: str) -> Optional[JWTToken]:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        user = self._users.get(user_id)
        if not user:
            return None

        access_token = self.create_access_token(user)
        return JWTToken(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )


class RBACManager:
    """Role-Based Access Control manager."""

    # Role hierarchy and permissions
    ROLE_PERMISSIONS = {
        UserRole.GUEST: [
            Permission.READ_PUBLIC,
        ],
        UserRole.USER: [
            Permission.READ_PUBLIC,
            Permission.READ_OWN,
            Permission.CREATE_PROJECT,
            Permission.READ_PROJECT,
            Permission.UPDATE_PROJECT,
            Permission.USE_API,
        ],
        UserRole.PREMIUM: [
            Permission.READ_PUBLIC,
            Permission.READ_OWN,
            Permission.CREATE_PROJECT,
            Permission.READ_PROJECT,
            Permission.UPDATE_PROJECT,
            Permission.DELETE_PROJECT,
            Permission.USE_API,
            Permission.HIGH_RATE_LIMIT,
        ],
        UserRole.ADMIN: [
            Permission.READ_PUBLIC,
            Permission.READ_OWN,
            Permission.CREATE_PROJECT,
            Permission.READ_PROJECT,
            Permission.UPDATE_PROJECT,
            Permission.DELETE_PROJECT,
            Permission.MANAGE_USERS,
            Permission.VIEW_ANALYTICS,
            Permission.USE_API,
            Permission.HIGH_RATE_LIMIT,
        ],
        UserRole.SYSTEM: [
            # All permissions
            Permission.READ_PUBLIC,
            Permission.READ_OWN,
            Permission.CREATE_PROJECT,
            Permission.READ_PROJECT,
            Permission.UPDATE_PROJECT,
            Permission.DELETE_PROJECT,
            Permission.MANAGE_USERS,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_ANALYTICS,
            Permission.USE_API,
            Permission.HIGH_RATE_LIMIT,
        ]
    }

    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        if not user or not user.is_active:
            return False

        user_permissions = RBACManager.ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions

    @staticmethod
    def has_any_permission(user: User, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(RBACManager.has_permission(user, perm) for perm in permissions)

    @staticmethod
    def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(RBACManager.has_permission(user, perm) for perm in permissions)

    @staticmethod
    def get_user_permissions(user: User) -> List[Permission]:
        """Get all permissions for a user."""
        if not user or not user.is_active:
            return []
        return RBACManager.ROLE_PERMISSIONS.get(user.role, [])

    @staticmethod
    def can_access_resource(user: User, resource_owner_id: str, required_permission: Permission) -> bool:
        """Check if user can access a specific resource."""
        # Check general permission
        if not RBACManager.has_permission(user, required_permission):
            return False

        # For own resources, check ownership
        if required_permission in [Permission.READ_OWN, Permission.UPDATE_PROJECT, Permission.DELETE_PROJECT]:
            return user.id == resource_owner_id

        return True


def require_auth(permissions: Optional[List[Permission]] = None):
    """Decorator to require authentication and permissions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from request context (FastAPI dependency injection)
            # This would be implemented in the FastAPI app
            user = kwargs.get('current_user')
            if not user:
                raise SecurityValidationError("Authentication required")

            # Check permissions if specified
            if permissions and not RBACManager.has_any_permission(user, permissions):
                SecurityAudit.log_security_event(
                    "PERMISSION_DENIED",
                    {"user_id": user.id, "required_permissions": [p.value for p in permissions]},
                    "WARNING"
                )
                raise SecurityValidationError("Insufficient permissions")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise SecurityValidationError("Authentication required")

            if user.role.value < required_role.value:  # Simple hierarchy check
                SecurityAudit.log_security_event(
                    "ROLE_DENIED",
                    {"user_id": user.id, "user_role": user.role.value, "required_role": required_role.value},
                    "WARNING"
                )
                raise SecurityValidationError(f"Role {required_role.value} required")

            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityHeaders:
    """Security headers for HTTP responses."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get OWASP recommended security headers."""
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # XSS protection
            "X-XSS-Protection": "1; mode=block",

            # HSTS (HTTP Strict Transport Security)
            "Strict-Transport-Security": "max-age=31536000; includeSubdomains",

            # Content Security Policy
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",

            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Feature Policy (permissions)
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",

            # Remove server information
            "Server": "NoLeet/1.0",
        }


# Password strength utilities
class PasswordPolicy:
    """Password strength validation and policies."""

    @staticmethod
    def validate_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return detailed feedback."""
        if len(password) < 8:
            return {"valid": False, "score": 0, "feedback": "Password too short"}

        score = 0
        feedback = []

        # Length check
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1

        # Character variety
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Add lowercase letters")

        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Add uppercase letters")

        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Add numbers")

        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Add special characters")

        # Common passwords check
        common_passwords = ["password", "123456", "qwerty", "admin"]
        if password.lower() in common_passwords:
            score = 0
            feedback = ["Password is too common"]

        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        strength_index = min(score, len(strength_levels) - 1)

        return {
            "valid": score >= 4,
            "score": score,
            "strength": strength_levels[strength_index],
            "feedback": feedback
        }


# Session management (basic implementation)
class SessionManager:
    """Session management for web applications."""

    def __init__(self, max_sessions_per_user: int = 5):
        self.max_sessions_per_user = max_sessions_per_user
        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_data

    def create_session(self, user: User, ip_address: str = None) -> str:
        """Create new session for user."""
        session_id = secrets.token_hex(32)

        # Clean up old sessions for this user
        user_sessions = [sid for sid, data in self._sessions.items() if data.get('user_id') == user.id]
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest sessions
            for sid in user_sessions[:len(user_sessions) - self.max_sessions_per_user + 1]:
                del self._sessions[sid]

        self._sessions[session_id] = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": None  # Would be set from request
        }

        SecurityAudit.log_security_event("SESSION_CREATED", {"user_id": user.id, "session_id": session_id})
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self._sessions.get(session_id)

    def update_session_activity(self, session_id: str):
        """Update last activity timestamp."""
        if session_id in self._sessions:
            self._sessions[session_id]["last_activity"] = datetime.utcnow()

    def destroy_session(self, session_id: str):
        """Destroy session."""
        if session_id in self._sessions:
            user_id = self._sessions[session_id]["user_id"]
            del self._sessions[session_id]
            SecurityAudit.log_security_event("SESSION_DESTROYED", {"user_id": user_id, "session_id": session_id})

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = [
            sid for sid, data in self._sessions.items()
            if data["last_activity"] < cutoff_time
        ]

        for sid in expired_sessions:
            del self._sessions[sid]

        if expired_sessions:
            SecurityAudit.log_security_event("EXPIRED_SESSIONS_CLEANED", {"count": len(expired_sessions)})


# Import re for regex validation
import re
