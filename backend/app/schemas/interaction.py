from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class InteractionCreate(BaseModel):
    item_id: int
    interaction_type: str = Field(..., pattern="^(view|like|dislike|hide)$")
    dwell_time_seconds: Optional[float] = 0.0

class InteractionResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    interaction_type: str
    dwell_time_seconds: float
    created_at: datetime

    class Config:
        from_attributes = True

class RatingCreate(BaseModel):
    item_id: int
    score: float = Field(..., ge=1.0, le=5.0)
    review: Optional[str] = None

class RatingResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    score: float
    review: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FavoriteToggle(BaseModel):
    item_id: int

class FavoriteResponse(BaseModel):
    item_id: int
    is_favorited: bool
    message: str

class SearchHistoryCreate(BaseModel):
    query: str

class SearchHistoryResponse(BaseModel):
    id: int
    query: str
    results_count: int
    created_at: datetime

    class Config:
        from_attributes = True
