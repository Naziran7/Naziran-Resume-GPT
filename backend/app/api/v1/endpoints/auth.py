from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.core.db import get_db
from app.core.limiter import limiter
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import TokenResponse, TokenRefreshRequest
from app.services.auth import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register a new user account."""
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_in)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Standard OAuth2 form-compatible login (used by Swagger UI)."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        email=form_data.username,
        plain_password=form_data.password
    )
    
    # Extract client IP and user agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.create_user_session(
        user_id=user.id,
        client_ip=client_ip,
        user_agent=user_agent
    )


@router.post("/login/json", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_json(
    request: Request,
    payload: dict,  # Expects {"email": "...", "password": "..."}
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Alternative JSON-payload login endpoint (recommended for frontend clients)."""
    email = payload.get("email")
    password = payload.get("password")
    
    from app.core.exceptions import BadRequestException
    if not email or not password:
        raise BadRequestException(message="Email and password are required fields.")
        
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(email=email, plain_password=password)
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.create_user_session(
        user_id=user.id,
        client_ip=client_ip,
        user_agent=user_agent
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Rotate JWT credentials using an active refresh token."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.refresh_user_session(
        refresh_token=payload.refresh_token,
        client_ip=client_ip,
        user_agent=user_agent
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Log out a user by revoking their session refresh token."""
    auth_service = AuthService(db)
    await auth_service.logout_user(refresh_token=payload.refresh_token)
    return {"success": True, "message": "Successfully logged out of session."}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Revoke all active sessions for the current user."""
    auth_service = AuthService(db)
    await auth_service.logout_everywhere(user_id=current_user.id)
    return {"success": True, "message": "Successfully logged out of all active devices."}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve details of the currently authenticated user."""
    return current_user
