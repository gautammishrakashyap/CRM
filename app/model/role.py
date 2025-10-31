from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler
from typing import List, Optional


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        json_schema = handler(schema)
        json_schema.update(type="string")
        return json_schema


class PermissionDB(BaseModel):
    """
    A Pydantic model representing a permission in the database.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Permission name (e.g., 'read_users', 'delete_posts')")
    resource: str = Field(..., description="Resource this permission applies to (e.g., 'users', 'posts')")
    action: str = Field(..., description="Action allowed (e.g., 'read', 'write', 'delete')")
    description: Optional[str] = Field(None, description="Human-readable description of the permission")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class RoleDB(BaseModel):
    """
    A Pydantic model representing a role in the database.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Role name (e.g., 'admin', 'user', 'moderator')")
    description: Optional[str] = Field(None, description="Human-readable description of the role")
    permissions: List[str] = Field(default=[], description="List of permission IDs assigned to this role")
    is_system_role: bool = Field(default=False, description="Whether this is a system-defined role")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserRoleDB(BaseModel):
    """
    A Pydantic model representing the many-to-many relationship between users and roles.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., description="User ID this role assignment belongs to")
    role_id: str = Field(..., description="Role ID assigned to the user")
    granted_by: str = Field(..., description="User ID of who granted this role")
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="When this role assignment expires (optional)")

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True