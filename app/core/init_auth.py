from typing import List
from pymongo import MongoClient
from app.core.config import (
    DEFAULT_PERMISSIONS, DEFAULT_ADMIN_ROLE, DEFAULT_USER_ROLE, DEFAULT_MODERATOR_ROLE, DEFAULT_STUDENT_ROLE,
    MONGO_COLLECTION_ROLES, MONGO_COLLECTION_PERMISSIONS, MONGO_COLLECTION_USER_ROLES
)
from app.repository.role import RoleRepository, PermissionRepository, UserRoleRepository
from app.model.role import RoleDB, PermissionDB, UserRoleDB
from app.core.security import get_password_hash
from app.model.user import UserDB
from app.repository.user import UserRepository
from app.core.config import MONGO_COLLECTION_USERS
import logging

logger = logging.getLogger(__name__)


class InitializationService:
    """Service to initialize default roles, permissions, and admin user"""
    
    def __init__(self, mongo_client: MongoClient):
        self.mongo_client = mongo_client
        self.role_repo = RoleRepository(mongo_client)
        self.permission_repo = PermissionRepository(mongo_client)
        self.user_role_repo = UserRoleRepository(mongo_client)
        self.user_repo = UserRepository(mongo_client)
    
    def initialize_permissions(self) -> List[str]:
        """Initialize default permissions and return their IDs"""
        permission_ids = []
        
        for perm_data in DEFAULT_PERMISSIONS:
            # Check if permission already exists
            existing_perm = self.permission_repo.get_permission_by_name(
                MONGO_COLLECTION_PERMISSIONS, 
                perm_data["name"]
            )
            
            if not existing_perm:
                # Create new permission
                permission = PermissionDB(**perm_data)
                created_perm = self.permission_repo.create_permission(
                    MONGO_COLLECTION_PERMISSIONS, 
                    permission
                )
                permission_ids.append(str(created_perm.id))
                logger.info(f"Created permission: {perm_data['name']}")
            else:
                permission_ids.append(str(existing_perm.id))
                logger.info(f"Permission already exists: {perm_data['name']}")
        
        return permission_ids
    
    def initialize_roles(self, permission_ids: List[str]) -> dict:
        """Initialize default roles and return their IDs"""
        role_ids = {}
        
        # Define role configurations
        role_configs = [
            {
                "name": DEFAULT_ADMIN_ROLE,
                "description": "Full system administrator with all permissions",
                "permissions": permission_ids,  # Admin gets all permissions
                "is_system_role": True
            },
            {
                "name": DEFAULT_MODERATOR_ROLE,
                "description": "Moderator with limited administrative permissions",
                "permissions": [pid for pid in permission_ids if not any(
                    perm["name"] in ["delete_users", "manage_roles"] 
                    for perm in DEFAULT_PERMISSIONS 
                    if str(pid) == str(pid)  # Filter out dangerous permissions
                )],
                "is_system_role": True
            },
            {
                "name": DEFAULT_USER_ROLE,
                "description": "Standard user with basic permissions",
                "permissions": [pid for pid in permission_ids if any(
                    perm["name"] in ["read_users", "read_posts", "write_posts"] 
                    for perm in DEFAULT_PERMISSIONS 
                    if str(pid) == str(pid)  # Basic user permissions
                )],
                "is_system_role": True
            },
            {
                "name": DEFAULT_STUDENT_ROLE,
                "description": "Student with profile management and application permissions",
                "permissions": [pid for pid in permission_ids if any(
                    perm["name"] in ["manage_profile", "upload_documents", "apply_colleges", "track_applications", "read_posts"] 
                    for perm in DEFAULT_PERMISSIONS 
                    if str(pid) == str(pid)  # Student permissions
                )],
                "is_system_role": True
            }
        ]
        
        for role_config in role_configs:
            # Check if role already exists
            existing_role = self.role_repo.get_role_by_name(
                MONGO_COLLECTION_ROLES, 
                role_config["name"]
            )
            
            if not existing_role:
                # Create new role
                role = RoleDB(**role_config)
                created_role = self.role_repo.create_role(MONGO_COLLECTION_ROLES, role)
                role_ids[role_config["name"]] = str(created_role.id)
                logger.info(f"Created role: {role_config['name']}")
            else:
                role_ids[role_config["name"]] = str(existing_role.id)
                logger.info(f"Role already exists: {role_config['name']}")
        
        return role_ids
    
    def create_admin_user(self, admin_role_id: str) -> UserDB:
        """Create default admin user if it doesn't exist"""
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = "admin123"  # Change this in production!
        
        # Check if admin user already exists
        existing_admin = self.user_repo.get_by_name(MONGO_COLLECTION_USERS, admin_username)
        
        if not existing_admin:
            # Create admin user
            admin_user = UserDB(
                email=admin_email,
                username=admin_username,
                hashed_password=get_password_hash(admin_password),
                is_active=True
            )
            created_admin = self.user_repo.create(admin_user, MONGO_COLLECTION_USERS)
            
            # Assign admin role to admin user
            user_role = UserRoleDB(
                user_id=str(created_admin.id),
                role_id=admin_role_id,
                granted_by=str(created_admin.id)  # Self-granted
            )
            self.user_role_repo.assign_role_to_user(MONGO_COLLECTION_USER_ROLES, user_role)
            
            logger.info(f"Created admin user: {admin_username}")
            logger.warning(f"Default admin password is '{admin_password}' - CHANGE THIS IN PRODUCTION!")
            return created_admin
        else:
            # Ensure existing admin has admin role
            admin_assignment = self.user_role_repo.get_user_role_assignment(
                MONGO_COLLECTION_USER_ROLES,
                str(existing_admin.id),
                admin_role_id
            )
            
            if not admin_assignment:
                user_role = UserRoleDB(
                    user_id=str(existing_admin.id),
                    role_id=admin_role_id,
                    granted_by=str(existing_admin.id)
                )
                self.user_role_repo.assign_role_to_user(MONGO_COLLECTION_USER_ROLES, user_role)
                logger.info(f"Assigned admin role to existing admin user: {admin_username}")
            
            logger.info(f"Admin user already exists: {admin_username}")
            return existing_admin
    
    def initialize_authorization_system(self) -> dict:
        """Initialize the complete authorization system"""
        logger.info("Starting authorization system initialization...")
        
        try:
            # Step 1: Initialize permissions
            permission_ids = self.initialize_permissions()
            logger.info(f"Initialized {len(permission_ids)} permissions")
            
            # Step 2: Initialize roles
            role_ids = self.initialize_roles(permission_ids)
            logger.info(f"Initialized {len(role_ids)} roles")
            
            # Step 3: Create admin user
            admin_user = self.create_admin_user(role_ids[DEFAULT_ADMIN_ROLE])
            
            logger.info("Authorization system initialization completed successfully")
            
            return {
                "permission_ids": permission_ids,
                "role_ids": role_ids,
                "admin_user_id": str(admin_user.id),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize authorization system: {str(e)}")
            raise


def initialize_auth_system(mongo_client: MongoClient) -> dict:
    """Convenience function to initialize the authorization system"""
    service = InitializationService(mongo_client)
    return service.initialize_authorization_system()