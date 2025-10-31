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


class UserDB(BaseModel):
    """
    A Pydantic model representing a user in the database.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: str
    hashed_password: str
    username: str
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ✅ Pydantic v2: serializer for ObjectId
    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    class Config:
        populate_by_name = True   # ✅ replaces allow_population_by_field_name
        arbitrary_types_allowed = True
