from typing import Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.session import UserSession
from app.repositories.base import BaseRepository

class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserSession, db)

    async def get_active_session_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """Fetch active session corresponding to a refresh token."""
        query = (
            select(UserSession)
            .where(UserSession.refresh_token == refresh_token)
            .where(UserSession.is_revoked == False)
            .where(UserSession.expires_at > datetime.now(timezone.utc))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        """Revoke a single session."""
        query = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(is_revoked=True)
        )
        await self.db.execute(query)

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> None:
        """Revoke all active sessions of a user (forced logout everywhere)."""
        query = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_revoked == False)
            .values(is_revoked=True)
        )
        await self.db.execute(query)
