from typing import List, Optional
from pydantic import BaseModel
from app.schemas.item import ItemResponse

class RecommendationExplanation(BaseModel):
    match_percentage: int
    score: float
    headline: str
    reasons: List[str]
    factor_weights: dict
    strategy: str

class RecommendedItem(BaseModel):
    item: ItemResponse
    score: float
    match_percentage: int
    explanation: RecommendationExplanation

class RecommendationFeedResponse(BaseModel):
    strategy: str
    title: str
    description: str
    items: List[RecommendedItem]

class DashboardRecommendationsResponse(BaseModel):
    recommended_for_you: List[RecommendedItem]
    trending_for_you: List[RecommendedItem]
    based_on_interests: List[RecommendedItem]
    recently_viewed: List[ItemResponse]
    popular_items: List[RecommendedItem]
