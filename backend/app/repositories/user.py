from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Role
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email, loading their associated role eagerly."""
        query = (
            select(User)
            .where(User.email == email)
            .where(User.deleted_at == None)
            .options(selectinload(User.role))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_with_role(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by ID, loading their associated role eagerly."""
        query = (
            select(User)
            .where(User.id == user_id)
            .where(User.deleted_at == None)
            .options(selectinload(User.role))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Fetch a role record by name (e.g. 'admin', 'user')."""
        query = select(Role).where(Role.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_role_if_not_exists(self, name: str, description: Optional[str] = None) -> Role:
        """Create a role helper to quickly populate initial values."""
        existing = await self.get_role_by_name(name)
        if existing:
            return existing
        role = Role(name=name, description=description)
        self.db.add(role)
        await self.db.flush()
        return role
