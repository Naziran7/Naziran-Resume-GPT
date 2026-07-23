import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException
from app.models.user import User
from app.models.session import UserSession
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.schemas.user import UserCreate
from app.schemas.token import TokenResponse

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    async def register_user(self, user_in: UserCreate) -> User:
        """Register a new user, seeding roles dynamically if necessary."""
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException(message="A user with this email address already exists.")

        # Ensure role exists and retrieve it
        role = await self.user_repo.create_role_if_not_exists(
            name=user_in.role_name, 
            description=f"Standard {user_in.role_name} permissions"
        )

        hashed = hash_password(user_in.password)
        
        user_data = {
            "email": user_in.email,
            "hashed_password": hashed,
            "full_name": user_in.full_name,
            "role_id": role.id,
            "is_active": True
        }
        
        user = await self.user_repo.create(user_data)
        await self.db.flush()
        # Fetch the complete user record with eagerly loaded role relationship
        db_user = await self.user_repo.get_by_email(user.email)
        return db_user

    async def authenticate_user(self, email: str, plain_password: str) -> User:
        """Validate user credentials."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException(message="Incorrect email or password.")
        
        if not user.is_active:
            raise UnauthorizedException(message="This user account has been deactivated.")

        if not verify_password(plain_password, user.hashed_password):
            raise UnauthorizedException(message="Incorrect email or password.")

        return user

    async def create_user_session(
        self, user_id: uuid.UUID, client_ip: Optional[str] = None, user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Create new access and refresh tokens and save the session details."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        # Calculate expiry
        from app.core.config import settings
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        session_data = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "is_revoked": False,
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        await self.session_repo.create(session_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def refresh_user_session(
        self, refresh_token: str, client_ip: Optional[str] = None, user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Rotate the refresh token (token rotation strategy) for maximum session security."""
        # 1. Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid or expired refresh token.")

        # 2. Check if session exists and is active in database
        session = await self.session_repo.get_active_session_by_token(refresh_token)
        if not session:
            raise UnauthorizedException(message="Session has been revoked or expired.")

        # 3. Perform Token Rotation: Revoke current session
        await self.session_repo.revoke_session(session.id)

        # 4. Generate new tokens and create a new session
        user_id = uuid.UUID(payload.get("sub"))
        return await self.create_user_session(user_id=user_id, client_ip=client_ip, user_agent=user_agent)

    async def logout_user(self, refresh_token: str) -> None:
        """Log the user out by revoking the corresponding session token."""
        session = await self.session_repo.get_active_session_by_token(refresh_token)
        if session:
            await self.session_repo.revoke_session(session.id)
            
    async def logout_everywhere(self, user_id: uuid.UUID) -> None:
        """Forcefully terminate all active sessions of a user."""
        await self.session_repo.revoke_all_user_sessions(user_id)
