from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Fetch a single record by UUID primary key."""
        query = select(self.model).where(self.model.id == id)
        # Handle soft deletes if the model supports it
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at == None)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        query = select(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at == None)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: Dict[str, Any] | ModelType) -> ModelType:
        """Create a new database record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """Update an existing record."""
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def delete(self, id: uuid.UUID) -> Optional[ModelType]:
        """Perform a hard delete of a record."""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
        return db_obj

    async def soft_delete(self, id: uuid.UUID) -> Optional[ModelType]:
        """Perform a soft delete by setting deleted_at to current time."""
        from datetime import datetime, timezone
        db_obj = await self.get(id)
        if db_obj and hasattr(db_obj, "deleted_at"):
            db_obj.deleted_at = datetime.now(timezone.utc)
            self.db.add(db_obj)
            await self.db.flush()
        return db_obj
