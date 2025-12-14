"""
Unit tests for security authentication functionality.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from noleet.app.core.security.auth import (
    AuthManager,
    RBACManager,
    User,
    UserRole,
    Permission,
    JWTToken,
    LoginRequest,
    RegisterRequest,
    PasswordPolicy,
    SessionManager,
    SecurityValidationError
)


class TestAuthManager:
    """Test authentication manager functionality."""

    def test_auth_manager_initialization(self):
        """Test auth manager initialization."""
        auth_manager = AuthManager()

        assert auth_manager._users == {}
        assert auth_manager._password_hashes == {}
        assert auth_manager.secret_key is not None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        auth_manager = AuthManager()

        password = "test_password_123"
        hashed = auth_manager.hash_password(password)

        assert hashed != password
        assert auth_manager.verify_password(password, hashed)
        assert not auth_manager.verify_password("wrong_password", hashed)

    def test_user_creation(self):
        """Test user creation."""
        auth_manager = AuthManager()

        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )

        user = auth_manager.create_user(register_request)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.id in auth_manager._users
        assert user.id in auth_manager._password_hashes

    def test_duplicate_user_creation(self):
        """Test duplicate user creation prevention."""
        auth_manager = AuthManager()

        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )

        # Create first user
        auth_manager.create_user(register_request)

        # Try to create duplicate
        with pytest.raises(SecurityValidationError):
            auth_manager.create_user(register_request)

    def test_user_authentication_success(self):
        """Test successful user authentication."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Authenticate
        authenticated_user = auth_manager.authenticate_user("testuser", "StrongPass123!")

        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.last_login is not None

    def test_user_authentication_failure(self):
        """Test failed user authentication."""
        auth_manager = AuthManager()

        # Try to authenticate non-existent user
        result = auth_manager.authenticate_user("nonexistent", "password")
        assert result is None

        # Try wrong password
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        auth_manager.create_user(register_request)

        result = auth_manager.authenticate_user("testuser", "wrongpassword")
        assert result is None

    def test_account_lockout(self):
        """Test account lockout after failed attempts."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Fail login multiple times
        for _ in range(5):
            auth_manager.authenticate_user("testuser", "wrongpassword")

        # Check that account is locked
        locked_user = auth_manager._users[user.id]
        assert locked_user.locked_until is not None
        assert locked_user.failed_login_attempts >= 5

    def test_jwt_token_creation(self):
        """Test JWT token creation."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Create token
        token = auth_manager.create_access_token(user)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user.id
        assert payload["username"] == user.username
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_jwt_token_verification(self):
        """Test JWT token verification."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Create and verify token
        token = auth_manager.create_access_token(user)
        payload = auth_manager.verify_token(token)

        assert payload["sub"] == user.id
        assert payload["username"] == user.username

        # Test invalid token
        invalid_payload = auth_manager.verify_token("invalid.token.here")
        assert invalid_payload is None

    def test_refresh_token_flow(self):
        """Test refresh token functionality."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Create refresh token
        refresh_token = auth_manager.create_refresh_token(user)
        assert refresh_token is not None

        # Use refresh token to get new access token
        new_token = auth_manager.refresh_access_token(refresh_token)
        assert new_token is not None
        assert isinstance(new_token, JWTToken)
        assert new_token.access_token is not None

        # Verify new access token works
        payload = auth_manager.verify_token(new_token.access_token)
        assert payload["sub"] == user.id

    def test_expired_token_handling(self):
        """Test expired token handling."""
        auth_manager = AuthManager()

        # Create user
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        user = auth_manager.create_user(register_request)

        # Create token with very short expiry
        short_lived_auth = AuthManager(access_token_expire_minutes=0)
        expired_token = short_lived_auth.create_access_token(user)

        # Token should be expired
        payload = auth_manager.verify_token(expired_token)
        assert payload is None


class TestRBACManager:
    """Test RBAC manager functionality."""

    def test_permission_checking(self):
        """Test permission checking."""
        # Create test user
        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        # User should have basic permissions
        assert RBACManager.has_permission(user, Permission.READ_PUBLIC)
        assert RBACManager.has_permission(user, Permission.READ_OWN)
        assert RBACManager.has_permission(user, Permission.CREATE_PROJECT)

        # User should not have admin permissions
        assert not RBACManager.has_permission(user, Permission.MANAGE_USERS)
        assert not RBACManager.has_permission(user, Permission.MANAGE_SYSTEM)

    def test_admin_permissions(self):
        """Test admin user permissions."""
        admin_user = User(
            id="admin-user",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN
        )

        # Admin should have all permissions
        assert RBACManager.has_permission(admin_user, Permission.MANAGE_USERS)
        assert RBACManager.has_permission(admin_user, Permission.MANAGE_SYSTEM)
        assert RBACManager.has_permission(admin_user, Permission.VIEW_ANALYTICS)

    def test_multiple_permissions_check(self):
        """Test checking multiple permissions."""
        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        # Check multiple permissions
        permissions = [Permission.READ_PUBLIC, Permission.CREATE_PROJECT]
        assert RBACManager.has_any_permission(user, permissions)
        assert RBACManager.has_all_permissions(user, permissions)

        # Check with some missing permissions
        permissions_with_admin = [Permission.READ_PUBLIC, Permission.MANAGE_USERS]
        assert RBACManager.has_any_permission(user, permissions_with_admin)
        assert not RBACManager.has_all_permissions(user, permissions_with_admin)

    def test_resource_access_control(self):
        """Test resource-specific access control."""
        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        # User should access their own resources
        assert RBACManager.can_access_resource(user, "test-user", Permission.UPDATE_PROJECT)

        # User should not access others' resources
        assert not RBACManager.can_access_resource(user, "other-user", Permission.UPDATE_PROJECT)

    def test_guest_user_permissions(self):
        """Test guest user permissions."""
        guest_user = User(
            id="guest-user",
            email="guest@example.com",
            username="guest",
            role=UserRole.GUEST
        )

        # Guest should only have public read access
        assert RBACManager.has_permission(guest_user, Permission.READ_PUBLIC)
        assert not RBACManager.has_permission(guest_user, Permission.CREATE_PROJECT)


class TestUserModel:
    """Test User model validation."""

    def test_valid_user_creation(self):
        """Test valid user creation."""
        user = User(
            id="test-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        assert user.id == "test-id"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.created_at is not None

    def test_invalid_username(self):
        """Test invalid username validation."""
        with pytest.raises(SecurityValidationError):
            User(
                id="test-id",
                email="test@example.com",
                username="us",  # Too short
                role=UserRole.USER
            )

    def test_invalid_email(self):
        """Test invalid email validation."""
        with pytest.raises(SecurityValidationError):
            User(
                id="test-id",
                email="invalid-email",
                username="testuser",
                role=UserRole.USER
            )


class TestRegisterRequest:
    """Test registration request validation."""

    def test_valid_registration(self):
        """Test valid registration request."""
        request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )

        assert request.email == "test@example.com"
        assert request.username == "testuser"

    def test_password_mismatch(self):
        """Test password mismatch validation."""
        with pytest.raises(SecurityValidationError):
            RegisterRequest(
                email="test@example.com",
                username="testuser",
                password="StrongPass123!",
                confirm_password="DifferentPass123!"
            )

    def test_weak_password(self):
        """Test weak password validation."""
        with pytest.raises(SecurityValidationError):
            RegisterRequest(
                email="test@example.com",
                username="testuser",
                password="weak",
                confirm_password="weak"
            )


class TestPasswordPolicy:
    """Test password policy validation."""

    def test_strong_password_validation(self):
        """Test strong password validation."""
        result = PasswordPolicy.validate_strength("StrongPass123!")

        assert result["valid"] is True
        assert result["score"] >= 4
        assert result["strength"] in ["Good", "Strong"]

    def test_weak_password_validation(self):
        """Test weak password validation."""
        result = PasswordPolicy.validate_strength("password")

        assert result["valid"] is False
        assert result["score"] < 4
        assert "common" in str(result["feedback"]).lower()

    def test_password_length_validation(self):
        """Test password length requirements."""
        short_password = PasswordPolicy.validate_strength("Short1!")
        assert short_password["valid"] is False

        long_password = PasswordPolicy.validate_strength("VeryLongPassword123456789!")
        assert long_password["score"] > short_password["score"]


class TestSessionManager:
    """Test session management functionality."""

    def test_session_creation(self):
        """Test session creation."""
        session_manager = SessionManager()

        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        session_id = session_manager.create_session(user, "192.168.1.1")

        assert session_id is not None
        session_data = session_manager.get_session(session_id)

        assert session_data["user_id"] == user.id
        assert session_data["username"] == user.username
        assert session_data["ip_address"] == "192.168.1.1"

    def test_session_activity_update(self):
        """Test session activity tracking."""
        session_manager = SessionManager()

        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        session_id = session_manager.create_session(user)
        original_session = session_manager.get_session(session_id)

        # Update activity
        session_manager.update_session_activity(session_id)
        updated_session = session_manager.get_session(session_id)

        assert updated_session["last_activity"] >= original_session["last_activity"]

    def test_session_cleanup(self):
        """Test expired session cleanup."""
        session_manager = SessionManager()

        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        # Create session
        session_id = session_manager.create_session(user)

        # Manually expire session by setting old time
        session_data = session_manager.get_session(session_id)
        session_data["last_activity"] = datetime.utcnow() - timedelta(hours=25)  # Very old

        # Run cleanup
        session_manager.cleanup_expired_sessions(max_age_hours=24)

        # Session should be gone
        assert session_manager.get_session(session_id) is None

    def test_max_sessions_per_user(self):
        """Test maximum sessions per user limit."""
        session_manager = SessionManager(max_sessions_per_user=2)

        user = User(
            id="test-user",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER
        )

        # Create maximum allowed sessions
        session1 = session_manager.create_session(user)
        session2 = session_manager.create_session(user)

        # Both should exist
        assert session_manager.get_session(session1) is not None
        assert session_manager.get_session(session2) is not None

        # Third session should remove oldest
        session3 = session_manager.create_session(user)

        # First session should be gone, others should remain
        assert session_manager.get_session(session1) is None
        assert session_manager.get_session(session2) is not None
        assert session_manager.get_session(session3) is not None
