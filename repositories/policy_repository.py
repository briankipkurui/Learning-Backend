from models import PolicyTypeModel, PolicyModel, PolicyAcknowledgementModel
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional

class PolicyRepository:
    def __init__(self, db: Session):
        """
        Initialize policy repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========== Policy Type Methods ==========
    
    def get_all_policy_types(self) -> List[PolicyTypeModel]:
        """
        Get all policy types.
        
        Returns:
            List of policy types
        """
        return self.db.query(PolicyTypeModel)\
            .order_by(PolicyTypeModel.name.asc())\
            .all()
    
    def get_policy_type_by_id(self, policy_type_id: UUID) -> Optional[PolicyTypeModel]:
        """
        Get a policy type by ID.
        
        Args:
            policy_type_id: UUID of the policy type
            
        Returns:
            PolicyTypeModel or None
        """
        return self.db.query(PolicyTypeModel)\
            .filter(PolicyTypeModel.Id == policy_type_id)\
            .first()
    
    def get_policy_type_by_name(self, name: str) -> Optional[PolicyTypeModel]:
        """
        Get a policy type by name.
        
        Args:
            name: Name of the policy type
            
        Returns:
            PolicyTypeModel or None
        """
        return self.db.query(PolicyTypeModel)\
            .filter(PolicyTypeModel.name == name)\
            .first()
    
    def get_policy_type_by_slug(self, slug: str) -> Optional[PolicyTypeModel]:
        """
        Get a policy type by slug.
        
        Args:
            slug: Slug of the policy type
            
        Returns:
            PolicyTypeModel or None
        """
        return self.db.query(PolicyTypeModel)\
            .filter(PolicyTypeModel.slug == slug)\
            .first()
    
    def create_policy_type(self, name: str, slug: str, description: str = None, is_required: bool = False) -> PolicyTypeModel:
        """
        Create a new policy type.
        
        Args:
            name: Policy type name
            slug: Policy type slug
            description: Policy type description
            is_required: Whether this policy type is required
            
        Returns:
            Created PolicyTypeModel
        """
        policy_type = PolicyTypeModel(
            name=name,
            slug=slug,
            description=description,
            is_required=is_required
        )
        self.db.add(policy_type)
        self.db.commit()
        self.db.refresh(policy_type)
        return policy_type
    
    def update_policy_type(
        self, 
        policy_type_id: UUID, 
        name: str = None,
        slug: str = None,
        description: str = None,
        is_required: bool = None
    ) -> Optional[PolicyTypeModel]:
        """
        Update a policy type.
        
        Args:
            policy_type_id: UUID of the policy type to update
            name: New policy type name
            slug: New policy type slug
            description: New policy type description
            is_required: Whether this policy type is required
            
        Returns:
            Updated PolicyTypeModel or None if not found
        """
        policy_type = self.get_policy_type_by_id(policy_type_id)
        
        if not policy_type:
            return None
        
        if name is not None:
            policy_type.name = name
        if slug is not None:
            policy_type.slug = slug
        if description is not None:
            policy_type.description = description
        if is_required is not None:
            policy_type.is_required = is_required
        
        self.db.commit()
        self.db.refresh(policy_type)
        return policy_type
    
    def delete_policy_type(self, policy_type_id: UUID) -> bool:
        """
        Delete a policy type.
        
        Args:
            policy_type_id: UUID of the policy type to delete
            
        Returns:
            True if deleted, False if not found
        """
        policy_type = self.get_policy_type_by_id(policy_type_id)
        
        if not policy_type:
            return False
        
        self.db.delete(policy_type)
        self.db.commit()
        return True
    
    # ========== Policy Methods ==========
    
    def get_all_policies(self, include_inactive: bool = False, policy_type_id: UUID = None) -> List[PolicyModel]:
        """
        Get all policies.
        
        Args:
            include_inactive: Whether to include inactive policies
            policy_type_id: Optional filter by policy type
            
        Returns:
            List of policies
        """
        query = self.db.query(PolicyModel)
        
        if not include_inactive:
            query = query.filter(PolicyModel.is_active == True)
        
        if policy_type_id:
            query = query.filter(PolicyModel.policy_type_id == policy_type_id)
        
        return query.order_by(PolicyModel.effective_date.desc()).all()
    
    def get_policy_by_id(self, policy_id: UUID) -> Optional[PolicyModel]:
        """
        Get a policy by ID.
        
        Args:
            policy_id: UUID of the policy
            
        Returns:
            PolicyModel or None
        """
        return self.db.query(PolicyModel)\
            .filter(PolicyModel.Id == policy_id)\
            .first()
    
    def get_active_policy_by_type(self, policy_type_id: UUID) -> Optional[PolicyModel]:
        """
        Get the currently active policy for a given type.
        
        Args:
            policy_type_id: UUID of the policy type
            
        Returns:
            PolicyModel or None
        """
        return self.db.query(PolicyModel)\
            .filter(
                PolicyModel.policy_type_id == policy_type_id,
                PolicyModel.is_active == True,
                PolicyModel.replaced_by_id == None
            )\
            .order_by(PolicyModel.effective_date.desc())\
            .first()
    
    def create_policy(
        self, 
        title: str, 
        version: str, 
        content: str, 
        effective_date, 
        policy_type_id: UUID
    ) -> PolicyModel:
        """
        Create a new policy.
        
        Args:
            title: Policy title
            version: Policy version
            content: Policy content
            effective_date: Policy effective date
            policy_type_id: Policy type ID
            
        Returns:
            Created PolicyModel
        """
        policy = PolicyModel(
            title=title,
            version=version,
            content=content,
            effective_date=effective_date,
            policy_type_id=policy_type_id,
            is_active=True
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy
    
    def update_policy(
        self,
        policy_id: UUID,
        title: str = None,
        version: str = None,
        content: str = None,
        effective_date = None,
        is_active: bool = None
    ) -> Optional[PolicyModel]:
        """
        Update a policy.
        
        Args:
            policy_id: UUID of the policy to update
            title: New policy title
            version: New policy version
            content: New policy content
            effective_date: New policy effective date
            is_active: New active status
            
        Returns:
            Updated PolicyModel or None if not found
        """
        policy = self.get_policy_by_id(policy_id)
        
        if not policy:
            return None
        
        if title is not None:
            policy.title = title
        if version is not None:
            policy.version = version
        if content is not None:
            policy.content = content
        if effective_date is not None:
            policy.effective_date = effective_date
        if is_active is not None:
            policy.is_active = is_active
        
        self.db.commit()
        self.db.refresh(policy)
        return policy
    
    def replace_policy(self, old_policy_id: UUID, new_policy_id: UUID) -> bool:
        """
        Mark an old policy as replaced by a new policy.
        
        Args:
            old_policy_id: UUID of the policy being replaced
            new_policy_id: UUID of the replacement policy
            
        Returns:
            True if successful, False if not found
        """
        old_policy = self.get_policy_by_id(old_policy_id)
        
        if not old_policy:
            return False
        
        old_policy.replaced_by_id = new_policy_id
        old_policy.is_active = False
        
        self.db.commit()
        return True
    
    def delete_policy(self, policy_id: UUID) -> bool:
        """
        Delete a policy.
        
        Args:
            policy_id: UUID of the policy to delete
            
        Returns:
            True if deleted, False if not found
        """
        policy = self.get_policy_by_id(policy_id)
        
        if not policy:
            return False
        
        self.db.delete(policy)
        self.db.commit()
        return True
    
    # ========== Policy Acknowledgement Methods ==========
    
    def get_required_active_policies(self) -> List[PolicyModel]:
        """
        Get all required and active policies.
        
        Returns:
            List of required active policies
        """
        return self.db.query(PolicyModel)\
            .join(PolicyTypeModel)\
            .filter(
                PolicyTypeModel.is_required == True,
                PolicyModel.is_active == True
            )\
            .all()
    
    def create_policy_acknowledgement(
        self,
        policy_id: UUID,
        user_id: UUID,
        user_ip_address: str = None,
        user_agent: str = None
    ) -> PolicyAcknowledgementModel:
        """
        Create a policy acknowledgement.
        
        Args:
            policy_id: Policy ID
            user_id: User ID
            user_ip_address: User's IP address
            user_agent: User's browser agent
            
        Returns:
            Created PolicyAcknowledgementModel
        """
        acknowledgement = PolicyAcknowledgementModel(
            policy_id=policy_id,
            user_id=user_id,
            user_ip_address=user_ip_address,
            user_agent=user_agent
        )
        self.db.add(acknowledgement)
        self.db.commit()
        self.db.refresh(acknowledgement)
        return acknowledgement
    
    def get_user_policy_acknowledgement(
        self,
        user_id: UUID,
        policy_id: UUID
    ) -> Optional[PolicyAcknowledgementModel]:
        """
        Get a user's acknowledgement for a specific policy.
        
        Args:
            user_id: User ID
            policy_id: Policy ID
            
        Returns:
            PolicyAcknowledgementModel or None
        """
        return self.db.query(PolicyAcknowledgementModel)\
            .filter(
                PolicyAcknowledgementModel.user_id == user_id,
                PolicyAcknowledgementModel.policy_id == policy_id
            )\
            .first()
