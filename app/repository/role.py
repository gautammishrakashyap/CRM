from typing import List, Optional, Dict, Any
from pymongo import MongoClient
import pymongo
from app.repository.base import BaseRepository
from app.model.role import RoleDB, PermissionDB, UserRoleDB
from app.schema.role import UpdateRoleRequest, UpdatePermissionRequest
from bson import ObjectId
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder


class RoleRepository(BaseRepository):
    """Repository for role management operations"""

    def __init__(self, mongo: MongoClient):
        """Initialize the RoleRepository with the MongoDB client."""
        super().__init__(mongo)

    def create(self, model, collection: str):
        """Create a new document in the specified collection"""
        model_in_json = jsonable_encoder(model)
        new_model = self.database[collection].insert_one(document=model_in_json)
        created_model = self.database[collection].find_one(
            {"_id": new_model.inserted_id}
        )
        return RoleDB(**created_model)

    def get_by_id(self, collection: str, id: str) -> Optional[RoleDB]:
        """Get a document by ID"""
        try:
            # First try to find by string ID (current database format)
            find_model = self.database[collection].find_one({"_id": id})
            if find_model:
                return RoleDB(**find_model)
            
            # If not found, try ObjectId format (for compatibility)
            if ObjectId.is_valid(id):
                find_model = self.database[collection].find_one({"_id": ObjectId(id)})
                if find_model:
                    return RoleDB(**find_model)
            
            return None
        except Exception as e:
            # Log the error for debugging
            print(f"Error in get_by_id: {e}")
            return None

    def get_list(self, collection: str, sort_field: str = "created_at", 
                 sort_order: int = pymongo.DESCENDING, skip: int = 0, limit: int = 1000):
        """Get a list of documents"""
        docs = self.database[collection].find({}).sort([(sort_field, sort_order)]).skip(skip).limit(limit)
        total = self.database[collection].count_documents(filter={})
        return [RoleDB(**doc) for doc in docs], total

    def create_role(self, collection: str, role: RoleDB) -> RoleDB:
        """Create a new role"""
        return self.create(role, collection)

    def get_role_by_name(self, collection: str, name: str) -> Optional[RoleDB]:
        """Get a role by name"""
        role_data = self.database[collection].find_one({"name": name})
        if role_data:
            return RoleDB(**role_data)
        return None

    def get_role_by_id(self, collection: str, role_id: str) -> Optional[RoleDB]:
        """Get a role by ID"""
        return self.get_by_id(collection, role_id)

    def update_role(self, collection: str, role_id: str, update_data: UpdateRoleRequest) -> Optional[RoleDB]:
        """Update a role"""
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            result = self.database[collection].find_one_and_update(
                {"_id": ObjectId(role_id)},
                {"$set": update_dict},
                return_document=True
            )
            if result:
                return RoleDB(**result)
        return None

    def delete_role(self, collection: str, role_id: str) -> bool:
        """Delete a role"""
        result = self.database[collection].delete_one({"_id": ObjectId(role_id)})
        return result.deleted_count > 0

    def get_roles_for_user(self, user_roles_collection: str, roles_collection: str, user_id: str) -> List[RoleDB]:
        """Get all roles assigned to a user"""
        # First get user role assignments
        user_role_assignments = self.database[user_roles_collection].find({"user_id": user_id})
        role_ids = [ObjectId(assignment["role_id"]) for assignment in user_role_assignments]
        
        # Then get the actual role documents
        roles_data = self.database[roles_collection].find({"_id": {"$in": role_ids}})
        return [RoleDB(**role_data) for role_data in roles_data]

    def add_permission_to_role(self, collection: str, role_id: str, permission_id: str) -> bool:
        """Add a permission to a role"""
        result = self.database[collection].update_one(
            {"_id": ObjectId(role_id)},
            {"$addToSet": {"permissions": permission_id}}
        )
        return result.modified_count > 0

    def remove_permission_from_role(self, collection: str, role_id: str, permission_id: str) -> bool:
        """Remove a permission from a role"""
        result = self.database[collection].update_one(
            {"_id": ObjectId(role_id)},
            {"$pull": {"permissions": permission_id}}
        )
        return result.modified_count > 0


class PermissionRepository(BaseRepository):
    """Repository for permission management operations"""

    def __init__(self, mongo: MongoClient):
        """Initialize the PermissionRepository with the MongoDB client."""
        super().__init__(mongo)

    def create(self, model, collection: str):
        """Create a new document in the specified collection"""
        model_in_json = jsonable_encoder(model)
        new_model = self.database[collection].insert_one(document=model_in_json)
        created_model = self.database[collection].find_one(
            {"_id": new_model.inserted_id}
        )
        return PermissionDB(**created_model)

    def get_by_id(self, collection: str, id: str) -> Optional[PermissionDB]:
        """Get a document by ID"""
        try:
            # First try to find by string ID (current database format)
            find_model = self.database[collection].find_one({"_id": id})
            if find_model:
                return PermissionDB(**find_model)
            
            # If not found, try ObjectId format (for compatibility)
            if ObjectId.is_valid(id):
                find_model = self.database[collection].find_one({"_id": ObjectId(id)})
                if find_model:
                    return PermissionDB(**find_model)
            
            return None
        except Exception as e:
            # Log the error for debugging
            print(f"Error in PermissionRepository.get_by_id: {e}")
            return None

    def get_list(self, collection: str, sort_field: str = "created_at", 
                 sort_order: int = pymongo.DESCENDING, skip: int = 0, limit: int = 1000):
        """Get a list of documents"""
        docs = self.database[collection].find({}).sort([(sort_field, sort_order)]).skip(skip).limit(limit)
        total = self.database[collection].count_documents(filter={})
        return [PermissionDB(**doc) for doc in docs], total

    def create_permission(self, collection: str, permission: PermissionDB) -> PermissionDB:
        """Create a new permission"""
        return self.create(permission, collection)

    def get_permission_by_name(self, collection: str, name: str) -> Optional[PermissionDB]:
        """Get a permission by name"""
        permission_data = self.database[collection].find_one({"name": name})
        if permission_data:
            return PermissionDB(**permission_data)
        return None

    def get_permission_by_id(self, collection: str, permission_id: str) -> Optional[PermissionDB]:
        """Get a permission by ID"""
        return self.get_by_id(collection, permission_id)

    def get_permissions_by_ids(self, collection: str, permission_ids: List[str]) -> List[PermissionDB]:
        """Get multiple permissions by their IDs"""
        try:
            # First try to find by string IDs (current database format)
            permissions_data = self.database[collection].find({"_id": {"$in": permission_ids}})
            results = [PermissionDB(**perm_data) for perm_data in permissions_data]
            
            # If we didn't find all permissions, try ObjectId format for the missing ones
            if len(results) < len(permission_ids):
                found_ids = [str(result.id) for result in results]
                missing_ids = [pid for pid in permission_ids if pid not in found_ids]
                
                # Try ObjectId format for missing IDs
                object_ids = []
                for pid in missing_ids:
                    if ObjectId.is_valid(pid):
                        object_ids.append(ObjectId(pid))
                
                if object_ids:
                    additional_data = self.database[collection].find({"_id": {"$in": object_ids}})
                    results.extend([PermissionDB(**perm_data) for perm_data in additional_data])
            
            return results
        except Exception as e:
            print(f"Error in get_permissions_by_ids: {e}")
            return []

    def update_permission(self, collection: str, permission_id: str, update_data: UpdatePermissionRequest) -> Optional[PermissionDB]:
        """Update a permission"""
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            result = self.database[collection].find_one_and_update(
                {"_id": ObjectId(permission_id)},
                {"$set": update_dict},
                return_document=True
            )
            if result:
                return PermissionDB(**result)
        return None

    def delete_permission(self, collection: str, permission_id: str) -> bool:
        """Delete a permission"""
        result = self.database[collection].delete_one({"_id": ObjectId(permission_id)})
        return result.deleted_count > 0

    def get_permissions_for_user(self, user_roles_collection: str, roles_collection: str, permissions_collection: str, user_id: str) -> List[PermissionDB]:
        """Get all permissions for a user through their roles"""
        # Get user's roles
        role_repo = RoleRepository(self.mongo_client)
        user_roles = role_repo.get_roles_for_user(user_roles_collection, roles_collection, user_id)
        
        # Collect all permission IDs from user's roles
        permission_ids = []
        for role in user_roles:
            permission_ids.extend(role.permissions)
        
        # Remove duplicates and get permission documents
        unique_permission_ids = list(set(permission_ids))
        if unique_permission_ids:
            return self.get_permissions_by_ids(permissions_collection, unique_permission_ids)
        return []


class UserRoleRepository(BaseRepository):
    """Repository for user-role assignment operations"""

    def __init__(self, mongo: MongoClient):
        """Initialize the UserRoleRepository with the MongoDB client."""
        super().__init__(mongo)

    def create(self, model, collection: str):
        """Create a new document in the specified collection"""
        model_in_json = jsonable_encoder(model)
        new_model = self.database[collection].insert_one(document=model_in_json)
        created_model = self.database[collection].find_one(
            {"_id": new_model.inserted_id}
        )
        return UserRoleDB(**created_model)

    def assign_role_to_user(self, collection: str, user_role: UserRoleDB) -> UserRoleDB:
        """Assign a role to a user"""
        return self.create(user_role, collection)

    def remove_role_from_user(self, collection: str, user_id: str, role_id: str) -> bool:
        """Remove a role from a user"""
        result = self.database[collection].delete_one({
            "user_id": user_id,
            "role_id": role_id
        })
        return result.deleted_count > 0

    def get_user_role_assignment(self, collection: str, user_id: str, role_id: str) -> Optional[UserRoleDB]:
        """Get a specific user-role assignment"""
        assignment_data = self.database[collection].find_one({
            "user_id": user_id,
            "role_id": role_id
        })
        if assignment_data:
            return UserRoleDB(**assignment_data)
        return None

    def get_user_role_assignments(self, collection: str, user_id: str) -> List[UserRoleDB]:
        """Get all role assignments for a user"""
        assignments_data = self.database[collection].find({"user_id": user_id})
        return [UserRoleDB(**assignment_data) for assignment_data in assignments_data]

    def get_role_assignments(self, collection: str, role_id: str) -> List[UserRoleDB]:
        """Get all user assignments for a role"""
        assignments_data = self.database[collection].find({"role_id": role_id})
        return [UserRoleDB(**assignment_data) for assignment_data in assignments_data]

    def user_has_role(self, collection: str, user_id: str, role_name: str, roles_collection: str) -> bool:
        """Check if a user has a specific role"""
        # First get the role ID by name
        role_repo = RoleRepository(self.mongo_client)
        role = role_repo.get_role_by_name(roles_collection, role_name)
        if not role:
            return False
        
        # Check if user has this role assigned
        assignment = self.get_user_role_assignment(collection, user_id, str(role.id))
        return assignment is not None

    def cleanup_expired_assignments(self, collection: str) -> int:
        """Remove expired role assignments"""
        current_time = datetime.now(timezone.utc)
        result = self.database[collection].delete_many({
            "expires_at": {"$lt": current_time}
        })
        return result.deleted_count