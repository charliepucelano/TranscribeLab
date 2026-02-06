from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, Annotated

# Helper for ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

class CustomTemplate(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    name: str
    language: str # "en" or "es"
    system_instruction: str
    description: Optional[str] = None

class CreateTemplateRequest(BaseModel):
    name: str
    language: str = "en"
    system_instruction: str
    description: Optional[str] = None

class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    system_instruction: Optional[str] = None
    description: Optional[str] = None
