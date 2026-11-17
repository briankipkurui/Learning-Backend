from models import ProfessionModel
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional

class ProfessionRepository:
    def __init__(self, db: Session):
        """
        Initialize profession repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_all_professions(self, include_inactive: bool = False) -> List[ProfessionModel]:
        """
        Get all professions.
        
        Args:
            include_inactive: Whether to include inactive professions
            
        Returns:
            List of professions
        """
        query = self.db.query(ProfessionModel)
        
        if not include_inactive:
            query = query.filter(ProfessionModel.is_active == True)
        
        return query.order_by(ProfessionModel.name.asc()).all()
    
    def get_profession_by_id(self, profession_id: UUID) -> Optional[ProfessionModel]:
        """
        Get a profession by ID.
        
        Args:
            profession_id: UUID of the profession
            
        Returns:
            ProfessionModel or None
        """
        return self.db.query(ProfessionModel)\
            .filter(ProfessionModel.Id == profession_id)\
            .first()
    
    def get_profession_by_name(self, name: str) -> Optional[ProfessionModel]:
        """
        Get a profession by name.
        
        Args:
            name: Name of the profession
            
        Returns:
            ProfessionModel or None
        """
        return self.db.query(ProfessionModel)\
            .filter(ProfessionModel.name == name)\
            .first()
    
    def create_profession(self, name: str, description: str = None) -> ProfessionModel:
        """
        Create a new profession.
        
        Args:
            name: Profession name
            description: Profession description
            
        Returns:
            Created ProfessionModel
        """
        profession = ProfessionModel(
            name=name,
            description=description,
            is_active=True
        )
        self.db.add(profession)
        self.db.commit()
        self.db.refresh(profession)
        return profession
    
    def update_profession(
        self,
        profession_id: UUID,
        name: str = None,
        description: str = None,
        is_active: bool = None
    ) -> Optional[ProfessionModel]:
        """
        Update a profession.
        
        Args:
            profession_id: UUID of the profession
            name: New name
            description: New description
            is_active: New active status
            
        Returns:
            Updated ProfessionModel or None
        """
        profession = self.get_profession_by_id(profession_id)
        if not profession:
            return None
        
        if name is not None:
            profession.name = name
        if description is not None:
            profession.description = description
        if is_active is not None:
            profession.is_active = is_active
        
        self.db.commit()
        self.db.refresh(profession)
        return profession
    
    def delete_profession(self, profession_id: UUID) -> bool:
        """
        Delete a profession (soft delete by setting is_active=False).
        
        Args:
            profession_id: UUID of the profession
            
        Returns:
            bool: True if deleted, False if not found
        """
        profession = self.get_profession_by_id(profession_id)
        if not profession:
            return False
        
        profession.is_active = False
        self.db.commit()
        return True
