"""Security utilities for DocuMind."""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for sensitive data
fernet = Fernet(settings.SECRET_KEY[:32].encode().ljust(32, b'\0'))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(api_key), hashed_key)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like API keys."""
    return fernet.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return fernet.decrypt(encrypted_data.encode()).decode()


def generate_webhook_secret() -> str:
    """Generate a webhook secret for GitHub/GitLab webhooks."""
    return secrets.token_hex(32)


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature (GitHub/GitLab)."""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def validate_repository_path(repo_path: str) -> bool:
    """Validate repository path for security."""
    # Check for dangerous patterns
    dangerous_patterns = [
        '..',  # Path traversal
        '~',   # Home directory
        '$',   # Environment variables
    ]

    for pattern in dangerous_patterns:
        if pattern in repo_path:
            return False

    return True


def rate_limit_key(identifier: str, action: str) -> str:
    """Generate rate limiting key."""
    return f"rate_limit:{action}:{identifier}"


def is_valid_url(url: str) -> bool:
    """Validate URL format and security."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False

        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            return False

        # Prevent localhost/private IPs in production
        if not settings.DEBUG:
            private_ips = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '172.', '192.168.']
            if any(ip in parsed.netloc for ip in private_ips):
                return False

        return True

    except Exception:
        return False
