from typing import List, Dict, Any
from pydantic import BaseModel

class CategoryStat(BaseModel):
    category_id: int
    category_name: str
    count: int
    percentage: float

class TagStat(BaseModel):
    tag: str
    count: int

class ActivityItem(BaseModel):
    id: int
    type: str
    item_title: str
    item_id: int
    timestamp: str
    details: str

class UserAIInsightsResponse(BaseModel):
    user_id: int
    user_name: str
    experience_level: str
    top_categories: List[CategoryStat]
    top_tags: List[TagStat]
    interaction_stats: Dict[str, int]
    recommendation_stats: Dict[str, Any]
    affinity_radar: List[Dict[str, Any]]
    recent_activity: List[ActivityItem]

class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_items: int
    total_categories: int
    total_interactions: int
    total_ratings: int
    total_favorites: int
    average_platform_rating: float
    most_popular_category: str
    most_viewed_items: List[Dict[str, Any]]
    most_liked_items: List[Dict[str, Any]]
    most_recommended_items: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    daily_interactions: List[Dict[str, Any]]
