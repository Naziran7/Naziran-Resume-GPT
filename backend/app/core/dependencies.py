import uuid
from typing import List, Optional
from fastapi import Depends, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

# OAuth2 schema for Swagger UI integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

async def get_current_user(
    token_header: Optional[str] = Depends(oauth2_scheme),
    token_query: Optional[str] = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to retrieve and validate the current user from the access token (Header or Query)."""
    token = token_header or token_query
    if not token:
        raise UnauthorizedException(
            message="Not authenticated",
            code="NOT_AUTHENTICATED"
        )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException(
            message="Could not validate credentials",
            code="INVALID_CREDENTIALS"
        )
    
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(
            message="Token payload is missing subject identity",
            code="INVALID_CREDENTIALS"
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(
            message="Malformed subject identity inside token",
            code="INVALID_CREDENTIALS"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_user_with_role(user_id)
    if not user:
        raise UnauthorizedException(
            message="The user belonging to this token no longer exists",
            code="USER_NOT_FOUND"
        )
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to check if the current user is active."""
    if not current_user.is_active:
        raise ForbiddenException(message="User account is inactive")
    return current_user


class RoleChecker:
    """Dependency checker to enforce Role-Based Access Control (RBAC)."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # Load user role name
        role_name = current_user.role.name if current_user.role else None
        if role_name not in self.allowed_roles:
            raise ForbiddenException(
                message=f"Access forbidden: requires one of the following roles: {', '.join(self.allowed_roles)}"
            )
        return current_user
