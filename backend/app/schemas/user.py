from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class UserPreferencesSchema(BaseModel):
    preferred_categories: List[str] = Field(default_factory=list)
    preferred_tags: List[str] = Field(default_factory=list)
    experience_level: str = "Intermediate"
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6)
    full_name: str
    role: str = "user"  # "user" or "admin"
    preferred_categories: Optional[List[str]] = None
    preferred_tags: Optional[List[str]] = None
    experience_level: Optional[str] = "Intermediate"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    preferences: Optional[UserPreferencesSchema] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
