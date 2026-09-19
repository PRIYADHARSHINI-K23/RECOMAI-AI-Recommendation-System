from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "sparkles"

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    items_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    title: str
    slug: str
    category_id: int
    description: str
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    difficulty_level: str = "Intermediate"
    url: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    url: Optional[str] = None

class ItemResponse(ItemBase):
    id: int
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    rating_avg: float
    rating_count: int
    views_count: int
    likes_count: int
    created_at: datetime
    updated_at: datetime
    is_liked: Optional[bool] = False
    is_favorited: Optional[bool] = False
    user_rating: Optional[float] = None

    class Config:
        from_attributes = True
