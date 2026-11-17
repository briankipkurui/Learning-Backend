from uuid import UUID
from typing import Dict, Any
from slugify import slugify
from repositories.policy_repository import PolicyRepository
from utils import get_logger

class PolicyService:
    def __init__(self, policy_repository: PolicyRepository):
        """
        Initialize policy service with repository dependency.
        
        Args:
            policy_repository: Repository for policy data access
        """
        self.logger = get_logger("app.services.policy")
        self.policy_repository = policy_repository
        
        self.logger.info("PolicyService initialized successfully")

    # ========== Policy Type Methods ==========
    
    def get_all_policy_types(self) -> Dict[str, Any]:
        """
        Get all policy types.
        
        Returns:
            Dict with success status and policy types list
        """
        try:
            policy_types = self.policy_repository.get_all_policy_types()
            
            return {
                "success": True,
                "data": policy_types,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching policy types: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving policy types",
                "status_code": 500
            }
    
    def get_policy_type_by_id(self, policy_type_id: UUID) -> Dict[str, Any]:
        """
        Get a policy type by ID.
        
        Args:
            policy_type_id: UUID of the policy type
            
        Returns:
            Dict with success status and policy type data
        """
        try:
            policy_type = self.policy_repository.get_policy_type_by_id(policy_type_id)
            
            if not policy_type:
                return {
                    "success": False,
                    "message": "Policy type not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": policy_type,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching policy type {policy_type_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving policy type",
                "status_code": 500
            }
    
    def create_policy_type(self, name: str, description: str = None, is_required: bool = False) -> Dict[str, Any]:
        """
        Create a new policy type.
        
        Args:
            name: Policy type name
            description: Policy type description
            is_required: Whether this policy type is required
            
        Returns:
            Dict with success status and created policy type
        """
        try:
            # Check if policy type with same name already exists
            existing_policy_type = self.policy_repository.get_policy_type_by_name(name)
            if existing_policy_type:
                return {
                    "success": False,
                    "message": f"Policy type with name '{name}' already exists",
                    "status_code": 400
                }
            
            # Generate slug from name
            slug = slugify(name)
            
            # Check if slug already exists
            existing_slug = self.policy_repository.get_policy_type_by_slug(slug)
            if existing_slug:
                return {
                    "success": False,
                    "message": f"Policy type with slug '{slug}' already exists",
                    "status_code": 400
                }
            
            policy_type = self.policy_repository.create_policy_type(name, slug, description, is_required)
            
            return {
                "success": True,
                "message": "Policy type created successfully",
                "data": policy_type,
                "status_code": 201
            }
        except Exception as e:
            self.logger.error(f"Error creating policy type: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while creating policy type",
                "status_code": 500
            }
    
    def update_policy_type(
        self, 
        policy_type_id: UUID, 
        name: str = None, 
        description: str = None,
        is_required: bool = None
    ) -> Dict[str, Any]:
        """
        Update a policy type.
        
        Args:
            policy_type_id: UUID of the policy type
            name: New policy type name
            description: New policy type description
            is_required: Whether this policy type is required
            
        Returns:
            Dict with success status and updated policy type
        """
        try:
            # Check if policy type exists
            policy_type = self.policy_repository.get_policy_type_by_id(policy_type_id)
            if not policy_type:
                return {
                    "success": False,
                    "message": "Policy type not found",
                    "status_code": 404
                }
            
            # Check if new name conflicts with existing policy type
            slug = None
            if name and name != policy_type.name:
                existing_policy_type = self.policy_repository.get_policy_type_by_name(name)
                if existing_policy_type:
                    return {
                        "success": False,
                        "message": f"Policy type with name '{name}' already exists",
                        "status_code": 400
                    }
                
                # Generate new slug from new name
                slug = self.generate_slug(name)
                
                # Check if new slug conflicts with existing policy type
                existing_slug = self.policy_repository.get_policy_type_by_slug(slug)
                if existing_slug and existing_slug.Id != policy_type_id:
                    return {
                        "success": False,
                        "message": f"Policy type with slug '{slug}' already exists",
                        "status_code": 400
                    }
            
            updated_policy_type = self.policy_repository.update_policy_type(
                policy_type_id, name, slug, description, is_required
            )
            
            return {
                "success": True,
                "message": "Policy type updated successfully",
                "data": updated_policy_type,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error updating policy type {policy_type_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while updating policy type",
                "status_code": 500
            }
    
    def delete_policy_type(self, policy_type_id: UUID) -> Dict[str, Any]:
        """
        Delete a policy type.
        
        Args:
            policy_type_id: UUID of the policy type
            
        Returns:
            Dict with success status
        """
        try:
            deleted = self.policy_repository.delete_policy_type(policy_type_id)
            
            if not deleted:
                return {
                    "success": False,
                    "message": "Policy type not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Policy type deleted successfully",
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error deleting policy type {policy_type_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while deleting policy type",
                "status_code": 500
            }
    
    # ========== Policy Methods ==========
    
    def get_all_policies(self, include_inactive: bool = False, policy_type_id: UUID = None) -> Dict[str, Any]:
        """
        Get all policies.
        
        Args:
            include_inactive: Whether to include inactive policies
            policy_type_id: Optional filter by policy type
            
        Returns:
            Dict with success status and policies list
        """
        try:
            policies = self.policy_repository.get_all_policies(include_inactive, policy_type_id)
            
            return {
                "success": True,
                "data": policies,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching policies: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving policies",
                "status_code": 500
            }
    
    def get_policy_by_id(self, policy_id: UUID) -> Dict[str, Any]:
        """
        Get a policy by ID.
        
        Args:
            policy_id: UUID of the policy
            
        Returns:
            Dict with success status and policy data
        """
        try:
            policy = self.policy_repository.get_policy_by_id(policy_id)
            
            if not policy:
                return {
                    "success": False,
                    "message": "Policy not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": policy,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving policy",
                "status_code": 500
            }
    
    def get_active_policy_by_type(self, policy_type_id: UUID) -> Dict[str, Any]:
        """
        Get the currently active policy for a given type.
        
        Args:
            policy_type_id: UUID of the policy type
            
        Returns:
            Dict with success status and policy data
        """
        try:
            policy = self.policy_repository.get_active_policy_by_type(policy_type_id)
            
            if not policy:
                return {
                    "success": False,
                    "message": "No active policy found for this type",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": policy,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching active policy for type {policy_type_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving active policy",
                "status_code": 500
            }
    
    def get_active_policy_by_type_slug(self, policy_type_slug: str) -> Dict[str, Any]:
        """
        Get the currently active policy for a given type using slug.
        
        Args:
            policy_type_slug: Slug of the policy type
            
        Returns:
            Dict with success status and policy data
        """
        try:
            # First get the policy type by slug
            policy_type = self.policy_repository.get_policy_type_by_slug(policy_type_slug)
            
            if not policy_type:
                return {
                    "success": False,
                    "message": "Policy type not found",
                    "status_code": 404
                }
            
            # Then get the active policy for that type
            policy = self.policy_repository.get_active_policy_by_type(policy_type.Id)
            
            if not policy:
                return {
                    "success": False,
                    "message": "No active policy found for this type",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": policy,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error fetching active policy for type slug {policy_type_slug}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while retrieving active policy",
                "status_code": 500
            }
    
    def create_policy(
        self, 
        title: str, 
        version: str, 
        content: str, 
        effective_date, 
        policy_type_id: UUID,
        replaces_policy_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Create a new policy.
        
        Args:
            title: Policy title
            version: Policy version
            content: Policy content
            effective_date: Policy effective date
            policy_type_id: Policy type ID
            replaces_policy_id: ID of the policy this new policy replaces (optional)
            
        Returns:
            Dict with success status and created policy
        """
        try:
            # Verify policy type exists
            policy_type = self.policy_repository.get_policy_type_by_id(policy_type_id)
            if not policy_type:
                return {
                    "success": False,
                    "message": "Policy type not found",
                    "status_code": 404
                }
            
            # If replacing an existing policy, verify it exists
            if replaces_policy_id:
                old_policy = self.policy_repository.get_policy_by_id(replaces_policy_id)
                if not old_policy:
                    return {
                        "success": False,
                        "message": "Policy to be replaced not found",
                        "status_code": 404
                    }
                
                # Verify the old policy is of the same type
                if old_policy.policy_type_id != policy_type_id:
                    return {
                        "success": False,
                        "message": "Cannot replace a policy of a different type",
                        "status_code": 400
                    }
            
            # Create the new policy
            policy = self.policy_repository.create_policy(
                title, version, content, effective_date, policy_type_id
            )
            
            # If replacing an existing policy, mark the old one as replaced
            if replaces_policy_id:
                success = self.policy_repository.replace_policy(replaces_policy_id, policy.Id)
                if not success:
                    self.logger.warning(f"Failed to mark policy {replaces_policy_id} as replaced")
            
            return {
                "success": True,
                "message": "Policy created successfully",
                "data": policy,
                "status_code": 201
            }
        except Exception as e:
            self.logger.error(f"Error creating policy: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while creating policy",
                "status_code": 500
            }
    
    def update_policy(
        self,
        policy_id: UUID,
        title: str = None,
        version: str = None,
        content: str = None,
        effective_date = None,
        is_active: bool = None
    ) -> Dict[str, Any]:
        """
        Update a policy.
        
        Args:
            policy_id: UUID of the policy
            title: New policy title
            version: New policy version
            content: New policy content
            effective_date: New policy effective date
            is_active: New active status
            
        Returns:
            Dict with success status and updated policy
        """
        try:
            # Check if policy exists
            policy = self.policy_repository.get_policy_by_id(policy_id)
            if not policy:
                return {
                    "success": False,
                    "message": "Policy not found",
                    "status_code": 404
                }
            
            updated_policy = self.policy_repository.update_policy(
                policy_id, title, version, content, effective_date, is_active
            )
            
            return {
                "success": True,
                "message": "Policy updated successfully",
                "data": updated_policy,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error updating policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while updating policy",
                "status_code": 500
            }
    
    def delete_policy(self, policy_id: UUID) -> Dict[str, Any]:
        """
        Delete a policy.
        
        Args:
            policy_id: UUID of the policy
            
        Returns:
            Dict with success status
        """
        try:
            deleted = self.policy_repository.delete_policy(policy_id)
            
            if not deleted:
                return {
                    "success": False,
                    "message": "Policy not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Policy deleted successfully",
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error deleting policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while deleting policy",
                "status_code": 500
            }
    
    # ========== Policy Acknowledgement Methods ==========
    
    def acknowledge_required_policies(
        self,
        user_id: UUID,
        user_ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Create acknowledgements for all required active policies for a user.
        
        Args:
            user_id: User ID
            user_ip_address: User's IP address
            user_agent: User's browser agent
            
        Returns:
            Dict with success status
        """
        try:
            # Get all required active policies
            required_policies = self.policy_repository.get_required_active_policies()
            
            if not required_policies:
                self.logger.info("No required policies to acknowledge")
                return {
                    "success": True,
                    "message": "No required policies to acknowledge",
                    "status_code": 200
                }
            
            # Create acknowledgements
            acknowledgements_created = 0
            for policy in required_policies:
                # Check if already acknowledged
                existing = self.policy_repository.get_user_policy_acknowledgement(user_id, policy.Id)
                if not existing:
                    self.policy_repository.create_policy_acknowledgement(
                        policy_id=policy.Id,
                        user_id=user_id,
                        user_ip_address=user_ip_address,
                        user_agent=user_agent
                    )
                    acknowledgements_created += 1
            
            self.logger.info(f"Created {acknowledgements_created} policy acknowledgements for user {user_id}")
            
            return {
                "success": True,
                "message": f"Acknowledged {acknowledgements_created} required policies",
                "data": {"acknowledged_count": acknowledgements_created},
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Error acknowledging required policies for user {user_id}: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while acknowledging policies",
                "status_code": 500
            }
