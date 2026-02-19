from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

from typing import Annotated, Any, Union
from pydantic import BaseModel, EmailStr, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetJsonSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.str_schema(),
                core_schema.is_instance_schema(ObjectId),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserBase(BaseModel):
    email: str
    is_superuser: bool = False
    force_password_change: bool = False

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str
    encrypted_master_key: str

    master_key_hash: str
    key_derivation_salt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_superuser: bool = False
    force_password_change: bool = False
    
class User(UserBase):
    id: PyObjectId = Field(alias="_id")
    is_active: bool
    is_superuser: bool = False
    force_password_change: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "ignore"

class UserRegistered(User):
    recovery_key: str
