"""Authentication and authorization for DocuMind."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token, verify_api_key
from app.db.session import get_db
from app.models.user import User, UserSession
from app.services.user_service import UserService

# Security schemes
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    token = credentials.credentials

    # Try JWT token first
    payload = decode_access_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            user_service = UserService(db)
            return await user_service.get_user_by_id(int(user_id))

    # Try API key
    user_service = UserService(db)
    return await user_service.get_user_by_api_key(token)


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Get current authenticated user or raise 401."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


def require_role(required_role: str):
    """Create a dependency that requires a specific role."""

    async def role_checker(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user

    return role_checker


def require_permission(permission: str):
    """Create a dependency that requires a specific permission."""

    async def permission_checker(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if not user.permissions or permission not in user.permissions:
            if user.role != "admin":  # Admins have all permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )
        return user

    return permission_checker


async def create_user_session(
    db: AsyncSession,
    user: User,
    request: Request,
) -> UserSession:
    """Create a new user session."""
    from app.core.security import generate_api_key

    session_id = generate_api_key()

    session = UserSession(
        user_id=user.id,
        session_id=session_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        device_info={
            "host": request.headers.get("host"),
            "accept": request.headers.get("accept"),
            "accept_language": request.headers.get("accept-language"),
        },
        expires_at=datetime.utcnow() + timedelta(hours=24),  # 24 hour sessions
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


async def validate_session(
    db: AsyncSession,
    session_id: str,
) -> Optional[User]:
    """Validate session and return user if valid."""
    from sqlalchemy import select

    query = select(UserSession).where(
        UserSession.session_id == session_id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow(),
    )

    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if session:
        # Update last activity
        session.last_activity_at = datetime.utcnow()
        await db.commit()

        # Get user
        user_service = UserService(db)
        return await user_service.get_user_by_id(session.user_id)

    return None


async def invalidate_session(
    db: AsyncSession,
    session_id: str,
) -> bool:
    """Invalidate a user session."""
    from sqlalchemy import select, update

    query = select(UserSession).where(UserSession.session_id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if session:
        session.is_active = False
        await db.commit()
        return True

    return False


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Clean up expired sessions. Returns number of sessions cleaned."""
    from sqlalchemy import update

    # Mark expired sessions as inactive
    stmt = (
        update(UserSession)
        .where(
            UserSession.expires_at <= datetime.utcnow(),
            UserSession.is_active == True,
        )
        .values(is_active=False)
    )

    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount()
