from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.template import CustomTemplate, CreateTemplateRequest, UpdateTemplateRequest
from app.services.templates import TEMPLATES
from app.core.database import db

router = APIRouter()

class TemplateResponse(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    system_instruction: str
    language: str
    is_custom: bool = False
    can_edit: bool = False

@router.get("", response_model=List[TemplateResponse])
async def list_templates(language: str = "en", current_user: User = Depends(get_current_user)):
    """
    List all available templates (Built-in + Custom).
    """
    results = []
    
    # 1. Built-in Templates
    lang_templates = TEMPLATES.get(language, TEMPLATES["en"])
    for name, tmpl in lang_templates.items():
        results.append(TemplateResponse(
            id=name, # Use name as ID for built-ins
            name=name,
            description=tmpl.system_instruction[:100] + "...",
            system_instruction=tmpl.system_instruction,
            language=language,
            is_custom=False
        ))
        
    # 2. Custom Templates
    # Assuming collection name is 'templates'
    cursor = db.get_db().templates.find({"user_id": str(current_user.id)})
    async for t in cursor:
        results.append(TemplateResponse(
            id=str(t["_id"]),
            name=t["name"],
            description=t.get("description"),
            system_instruction=t["system_instruction"],
            language=t["language"],
            is_custom=True,
            can_edit=True
        ))
        
    return results

@router.post("/", response_model=CustomTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(request: CreateTemplateRequest, current_user: User = Depends(get_current_user)):
    new_template = CustomTemplate(
        user_id=str(current_user.id),
        name=request.name,
        language=request.language,
        system_instruction=request.system_instruction,
        description=request.description
    )
    
    result = await db.get_db().templates.insert_one(new_template.model_dump(by_alias=True, exclude={"id"}))
    return await db.get_db().templates.find_one({"_id": result.inserted_id})

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str, current_user: User = Depends(get_current_user)):
    # Verify ID format
    if not ObjectId.is_valid(template_id):
        raise HTTPException(status_code=400, detail="Invalid template ID")
        
    result = await db.get_db().templates.delete_one({
        "_id": ObjectId(template_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or not authorized")
        
@router.put("/{template_id}", response_model=CustomTemplate)
async def update_template(template_id: str, request: UpdateTemplateRequest, current_user: User = Depends(get_current_user)):
    if not ObjectId.is_valid(template_id):
        raise HTTPException(status_code=400, detail="Invalid template ID")
        
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    result = await db.get_db().templates.update_one(
        {"_id": ObjectId(template_id), "user_id": str(current_user.id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or not authorized")
        
    return await db.get_db().templates.find_one({"_id": ObjectId(template_id)})
