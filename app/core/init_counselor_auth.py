"""
Script to initialize counselor role and permissions in the database.
This should be run once to set up the counselor authorization system.
"""

from datetime import datetime, timezone
from app.core.database import DatabaseManager
from app.repository.role import RoleRepository
from app.model.role import RoleDB, PermissionDB
import logging

logger = logging.getLogger(__name__)


def initialize_counselor_authorization():
    """Initialize counselor role and permissions"""
    try:
        # Initialize database and repository
        database_manager = DatabaseManager()
        mongo_client = database_manager.get_mongo_client()
        role_repo = RoleRepository(mongo_client)
        
        # Define counselor permissions
        counselor_permissions = [
            {
                "name": "manage_leads",
                "resource": "leads",
                "action": "manage",
                "description": "Full access to manage leads - view, update, reassign, quality marking"
            },
            {
                "name": "view_own_profile",
                "resource": "counselor_profile",
                "action": "read",
                "description": "View own counselor profile"
            },
            {
                "name": "update_own_profile",
                "resource": "counselor_profile", 
                "action": "write",
                "description": "Update own counselor profile, working hours, preferences"
            },
            {
                "name": "log_communications",
                "resource": "communications",
                "action": "create",
                "description": "Log calls and messages with leads"
            },
            {
                "name": "view_dashboard",
                "resource": "dashboard",
                "action": "read", 
                "description": "View counselor dashboard and statistics"
            },
            {
                "name": "send_messages",
                "resource": "messages",
                "action": "create",
                "description": "Send emails, SMS, WhatsApp messages to leads"
            },
            {
                "name": "schedule_follow_ups",
                "resource": "follow_ups",
                "action": "manage",
                "description": "Schedule and manage follow-up appointments with leads"
            },
            {
                "name": "view_notifications",
                "resource": "notifications",
                "action": "read",
                "description": "View counselor notifications"
            }
        ]
        
        # Create permissions if they don't exist
        permission_ids = []
        for perm_data in counselor_permissions:
            # Check if permission already exists
            existing_perm = role_repo.database["permissions"].find_one({
                "name": perm_data["name"],
                "resource": perm_data["resource"]
            })
            
            if existing_perm:
                permission_ids.append(str(existing_perm["_id"]))
                logger.info(f"Permission {perm_data['name']} already exists")
            else:
                # Create new permission
                permission = PermissionDB(**perm_data)
                result = role_repo.create(permission.model_dump(by_alias=True), "permissions")
                if result:
                    permission_ids.append(str(result["_id"]))
                    logger.info(f"Created permission: {perm_data['name']}")
                else:
                    logger.error(f"Failed to create permission: {perm_data['name']}")
        
        # Create counselor role if it doesn't exist
        existing_role = role_repo.database["roles"].find_one({"name": "counselor"})
        
        if existing_role:
            logger.info("Counselor role already exists")
            # Update permissions if needed
            role_repo.database["roles"].update_one(
                {"_id": existing_role["_id"]},
                {"$set": {"permissions": permission_ids}}
            )
            logger.info("Updated counselor role permissions")
        else:
            # Create new counselor role
            counselor_role = RoleDB(
                name="counselor",
                description="Counselor role with access to lead management, communications, and dashboard",
                permissions=permission_ids,
                is_system_role=True
            )
            
            result = role_repo.create(counselor_role.model_dump(by_alias=True), "roles")
            if result:
                logger.info("Created counselor role successfully")
            else:
                logger.error("Failed to create counselor role")
        
        logger.info("Counselor authorization initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing counselor authorization: {str(e)}")
        return False


def assign_counselor_role_to_user(user_id: str, granted_by_user_id: str):
    """Assign counselor role to a user"""
    try:
        # Initialize database and repository
        database_manager = DatabaseManager()
        mongo_client = database_manager.get_mongo_client()
        role_repo = RoleRepository(mongo_client)
        
        # Get counselor role
        counselor_role = role_repo.database["roles"].find_one({"name": "counselor"})
        
        if not counselor_role:
            logger.error("Counselor role not found. Please run initialize_counselor_authorization first.")
            return False
        
        # Check if user already has counselor role
        existing_assignment = role_repo.database["user_roles"].find_one({
            "user_id": user_id,
            "role_id": str(counselor_role["_id"])
        })
        
        if existing_assignment:
            logger.info(f"User {user_id} already has counselor role")
            return True
        
        # Assign role to user
        from app.model.role import UserRoleDB
        user_role = UserRoleDB(
            user_id=user_id,
            role_id=str(counselor_role["_id"]),
            granted_by=granted_by_user_id
        )
        
        result = role_repo.create(user_role.model_dump(by_alias=True), "user_roles")
        if result:
            logger.info(f"Successfully assigned counselor role to user {user_id}")
            return True
        else:
            logger.error(f"Failed to assign counselor role to user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error assigning counselor role: {str(e)}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize counselor authorization
    print("Initializing counselor authorization system...")
    success = initialize_counselor_authorization()
    
    if success:
        print("✅ Counselor authorization system initialized successfully!")
        print("\nTo assign counselor role to a user, use:")
        print("assign_counselor_role_to_user(user_id, granted_by_user_id)")
    else:
        print("❌ Failed to initialize counselor authorization system")