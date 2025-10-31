from typing import Any
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic models"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
            raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId type")

    def __repr__(self):
        return f"PyObjectId('{self}')"


class BaseDBModel(BaseModel):
    """Base model for database entities"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps"""
    created_at: Any = Field(default_factory=lambda: ObjectId().generation_time)
    updated_at: Any = Field(default_factory=lambda: ObjectId().generation_time)


class Gender:
    """Gender constants"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    
    @classmethod
    def choices(cls):
        return [cls.MALE, cls.FEMALE, cls.OTHER]