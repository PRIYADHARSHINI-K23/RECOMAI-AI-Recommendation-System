from collections import Counter
from datetime import timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.user import User
from app.models.item import Item, Category
from app.models.interaction import Interaction, Rating, Favorite, SearchHistory
from app.models.recommendation import RecommendationLog
from app.schemas.analytics import UserAIInsightsResponse, CategoryStat, TagStat, ActivityItem
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/insights", tags=["AI Insights"])

@router.get("/me", response_model=UserAIInsightsResponse)
def get_user_ai_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve comprehensive AI insights, behavioral profile, and affinity breakdown for user."""
    # 1. Total counts
    views_count = db.query(func.count(Interaction.id)).filter(
        Interaction.user_id == current_user.id, Interaction.interaction_type == "view"
    ).scalar() or 0

    likes_count = db.query(func.count(Interaction.id)).filter(
        Interaction.user_id == current_user.id, Interaction.interaction_type == "like"
    ).scalar() or 0

    ratings_count = db.query(func.count(Rating.id)).filter(
        Rating.user_id == current_user.id
    ).scalar() or 0

    favorites_count = db.query(func.count(Favorite.id)).filter(
        Favorite.user_id == current_user.id
    ).scalar() or 0

    searches_count = db.query(func.count(SearchHistory.id)).filter(
        SearchHistory.user_id == current_user.id
    ).scalar() or 0

    # 2. Category affinities from views and likes
    interactions = db.query(Interaction).filter(Interaction.user_id == current_user.id).all()
    item_ids = [i.item_id for i in interactions]
    
    cat_counter = Counter()
    tag_counter = Counter()

    if item_ids:
        interacted_items = db.query(Item).filter(Item.id.in_(item_ids)).all()
        for item in interacted_items:
            if item.category:
                cat_counter[item.category.name] += 1
            for t in (item.tags or []):
                tag_counter[t.lower()] += 1

    # Include explicit preferences in counts
    if current_user.preferences:
        for c in (current_user.preferences.preferred_categories or []):
            cat_counter[str(c)] += 2
        for t in (current_user.preferences.preferred_tags or []):
            tag_counter[str(t).lower()] += 3

    total_cat_weight = sum(cat_counter.values()) or 1
    top_categories = []
    for cat_name, count in cat_counter.most_common(5):
        top_categories.append(CategoryStat(
            category_id=0,
            category_name=cat_name,
            count=count,
            percentage=round((count / total_cat_weight) * 100, 1)
        ))

    top_tags = []
    for tag_name, count in tag_counter.most_common(8):
        top_tags.append(TagStat(tag=tag_name, count=count))

    # 3. Radar Affinity dimensions
    affinity_dimensions = [
        {"dimension": "Machine Learning & AI", "score": min(98, 40 + cat_counter.get("Artificial Intelligence", 0) * 10 + tag_counter.get("python", 0) * 5)},
        {"dimension": "Web & Backend", "score": min(95, 35 + cat_counter.get("Web Engineering", 0) * 10 + tag_counter.get("fastapi", 0) * 8)},
        {"dimension": "Cloud & DevOps", "score": min(90, 30 + cat_counter.get("Cloud & DevOps", 0) * 10 + tag_counter.get("docker", 0) * 7)},
        {"dimension": "Data Science", "score": min(92, 35 + cat_counter.get("Data Science", 0) * 10 + tag_counter.get("sql", 0) * 6)},
        {"dimension": "Cyber Security", "score": min(85, 25 + cat_counter.get("Cyber Security", 0) * 12)},
        {"dimension": "Systems & Mojo", "score": min(90, 30 + cat_counter.get("Systems & Algorithms", 0) * 10 + tag_counter.get("mojo", 0) * 10)},
    ]

    # 4. Recent activity log
    recent_activity: List[ActivityItem] = []
    recent_views = db.query(Interaction).filter(
        Interaction.user_id == current_user.id
    ).order_by(Interaction.created_at.desc()).limit(8).all()

    for v in recent_views:
        item = v.item
        if item:
            dt = v.created_at
            if dt is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                iso_ts = dt.isoformat().replace("+00:00", "Z")
            else:
                iso_ts = ""

            recent_activity.append(ActivityItem(
                id=v.id,
                type=v.interaction_type.upper(),
                item_title=item.title,
                item_id=item.id,
                timestamp=iso_ts,
                details=f"{v.interaction_type.capitalize()} on '{item.title}'"
            ))

    # 5. Recommendation metrics from database
    rec_count = db.query(func.count(RecommendationLog.id)).filter(
        RecommendationLog.user_id == current_user.id
    ).scalar() or 0

    avg_match_query = db.query(func.avg(RecommendationLog.match_percentage)).filter(
        RecommendationLog.user_id == current_user.id
    ).scalar()
    avg_match_pct = int(round(avg_match_query)) if avg_match_query else 90

    recommendation_stats = {
        "total_recommendations_served": rec_count,
        "avg_match_percentage": avg_match_pct,
        "active_strategy": "Multi-Signal Hybrid (MAX + Mojo)",
        "learning_status": "Adaptive (Active signals logged)" if (views_count + likes_count) > 0 else "Cold-Start Initialized"
    }

    return UserAIInsightsResponse(
        user_id=current_user.id,
        user_name=current_user.full_name,
        experience_level=current_user.preferences.experience_level if current_user.preferences else "Intermediate",
        top_categories=top_categories,
        top_tags=top_tags,
        interaction_stats={
            "views": views_count,
            "likes": likes_count,
            "ratings": ratings_count,
            "favorites": favorites_count,
            "searches": searches_count
        },
        recommendation_stats=recommendation_stats,
        affinity_radar=affinity_dimensions,
        recent_activity=recent_activity
    )
