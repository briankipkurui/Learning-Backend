from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from models.database import Base
import uuid

class BaseModel(Base):
    """
    Base model class that other models inherit from.
    Contains common fields that most models need.
    """
    __abstract__ = True
    
    Id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<{self.__class__.__name__}(Id={self.Id})>"
