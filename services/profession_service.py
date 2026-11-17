from uuid import UUID
from typing import Dict, Any
from repositories import ProfessionRepository
from utils import get_logger

class ProfessionService:
    def __init__(self, profession_repository: ProfessionRepository):
        """
        Initialize profession service with repository dependency.
        
        Args:
            profession_repository: Repository for profession data access
        """
        self.logger = get_logger("app.services.profession")
        self.profession_repository = profession_repository
        
        self.logger.info("ProfessionService initialized successfully")
    
    def get_all_professions(self, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Get all professions.
        
        Args:
            include_inactive: Whether to include inactive professions
            
        Returns:
            Dict with success status and professions list
        """
        try:
            professions = self.profession_repository.get_all_professions(include_inactive)
            
            professions_data = [
                {
                    "Id": str(profession.Id),
                    "name": profession.name,
                    "description": profession.description,
                    "is_active": profession.is_active,
                    "created_at": profession.created_at.isoformat() if profession.created_at else None,
                    "updated_at": profession.updated_at.isoformat() if profession.updated_at else None
                }
                for profession in professions
            ]
            
            return {
                "success": True,
                "data": professions_data,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching professions: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving professions",
                "status_code": 500
            }
    
    def get_profession_by_id(self, profession_id: UUID) -> Dict[str, Any]:
        """
        Get a profession by ID.
        
        Args:
            profession_id: UUID of the profession
            
        Returns:
            Dict with success status and profession data
        """
        try:
            profession = self.profession_repository.get_profession_by_id(profession_id)
            
            if not profession:
                return {
                    "success": False,
                    "message": "Profession not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": {
                    "Id": str(profession.Id),
                    "name": profession.name,
                    "description": profession.description,
                    "is_active": profession.is_active,
                    "created_at": profession.created_at.isoformat() if profession.created_at else None,
                    "updated_at": profession.updated_at.isoformat() if profession.updated_at else None
                },
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching profession {profession_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving profession",
                "status_code": 500
            }
    
    def create_profession(self, name: str, description: str = None) -> Dict[str, Any]:
        """
        Create a new profession (Admin only).
        
        Args:
            name: Profession name
            description: Profession description
            
        Returns:
            Dict with success status and profession data
        """
        try:
            # Check if profession with same name already exists
            existing = self.profession_repository.get_profession_by_name(name)
            if existing:
                return {
                    "success": False,
                    "message": "A profession with this name already exists",
                    "status_code": 400
                }
            
            profession = self.profession_repository.create_profession(
                name=name,
                description=description
            )
            
            return {
                "success": True,
                "message": "Profession created successfully",
                "data": {
                    "Id": str(profession.Id),
                    "name": profession.name,
                    "description": profession.description,
                    "is_active": profession.is_active,
                    "created_at": profession.created_at.isoformat() if profession.created_at else None
                },
                "status_code": 201
            }
        except Exception as e:
            self.logger.error(f"Error creating profession: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred while creating profession: {str(e)}",
                "status_code": 500
            }
    
    def update_profession(
        self,
        profession_id: UUID,
        name: str = None,
        description: str = None,
        is_active: bool = None
    ) -> Dict[str, Any]:
        """
        Update a profession (Admin only).
        
        Args:
            profession_id: UUID of the profession
            name: New name
            description: New description
            is_active: New active status
            
        Returns:
            Dict with success status and updated profession data
        """
        try:
            # If updating name, check if another profession has that name
            if name is not None:
                existing = self.profession_repository.get_profession_by_name(name)
                if existing and str(existing.Id) != str(profession_id):
                    return {
                        "success": False,
                        "message": "A profession with this name already exists",
                        "status_code": 400
                    }
            
            profession = self.profession_repository.update_profession(
                profession_id=profession_id,
                name=name,
                description=description,
                is_active=is_active
            )
            
            if not profession:
                return {
                    "success": False,
                    "message": "Profession not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Profession updated successfully",
                "data": {
                    "Id": str(profession.Id),
                    "name": profession.name,
                    "description": profession.description,
                    "is_active": profession.is_active,
                    "updated_at": profession.updated_at.isoformat() if profession.updated_at else None
                },
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error updating profession {profession_id}: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred while updating profession: {str(e)}",
                "status_code": 500
            }
    
    def delete_profession(self, profession_id: UUID) -> Dict[str, Any]:
        """
        Delete a profession (Admin only).
        Performs soft delete by setting is_active=False.
        
        Args:
            profession_id: UUID of the profession
            
        Returns:
            Dict with success status
        """
        try:
            deleted = self.profession_repository.delete_profession(profession_id)
            
            if not deleted:
                return {
                    "success": False,
                    "message": "Profession not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Profession deleted successfully",
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error deleting profession {profession_id}: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred while deleting profession: {str(e)}",
                "status_code": 500
            }
