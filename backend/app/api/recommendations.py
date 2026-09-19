from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.item import Item
from app.schemas.recommendation import (
    DashboardRecommendationsResponse, RecommendationFeedResponse, RecommendedItem
)
from app.recommendation.engine import RecommendationEngine
from app.auth.dependencies import get_current_user_optional, get_current_user
from app.ai.max_service import max_service
from app.mojo.bridge import mojo_bridge

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])

@router.get("/dashboard", response_model=DashboardRecommendationsResponse)
def get_dashboard_recommendations(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve full personalized dashboard sections powered by MAX & Mojo."""
    engine = RecommendationEngine(db)

    # 1. Main Personalized Feed
    rec_for_you = engine.get_personalized_recommendations(current_user, limit=8, strategy="hybrid")

    # 2. Trending For You
    trending = engine.get_trending_recommendations(current_user, limit=6)

    # 3. Based On Your Interests
    based_on_interests = []
    if current_user and current_user.preferences:
        based_on_interests = engine.get_interest_based_recommendations(current_user, limit=6)
    else:
        based_on_interests = trending[:6]

    # 4. Recently Viewed
    recently_viewed = []
    if current_user:
        recently_viewed = engine.get_recently_viewed(current_user, limit=6)

    # 5. Popular Items
    popular = engine.get_trending_recommendations(None, limit=6)

    return DashboardRecommendationsResponse(
        recommended_for_you=rec_for_you,
        trending_for_you=trending,
        based_on_interests=based_on_interests,
        recently_viewed=recently_viewed,
        popular_items=popular
    )

@router.get("/feed", response_model=RecommendationFeedResponse)
def get_custom_feed(
    strategy: str = Query("hybrid", pattern="^(hybrid|preference|trending|interaction)$"),
    limit: int = 15,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve a custom recommendation feed using a chosen strategy."""
    engine = RecommendationEngine(db)
    
    titles = {
        "hybrid": "Hyper-Personalized Feed",
        "preference": "Tailored to Your Learning Interests",
        "trending": "Trending in Computer Science & AI",
        "interaction": "Inspired by Your Recent Activity"
    }
    descriptions = {
        "hybrid": "Multi-signal AI recommendations combining your explicit preferences, MAX embeddings, and Mojo similarity.",
        "preference": "Directly matches the categories and skill tags you selected in your profile.",
        "trending": "Items with high community momentum, bookmark velocity, and exceptional ratings.",
        "interaction": "Curated by analyzing items you liked, favorited, or engaged with recently."
    }

    if strategy == "trending":
        items = engine.get_trending_recommendations(current_user, limit=limit)
    elif strategy == "preference" and current_user:
        items = engine.get_interest_based_recommendations(current_user, limit=limit)
    else:
        items = engine.get_personalized_recommendations(current_user, limit=limit, strategy=strategy)

    return RecommendationFeedResponse(
        strategy=strategy,
        title=titles.get(strategy, "Recommendations"),
        description=descriptions.get(strategy, ""),
        items=items
    )

@router.get("/item/{item_id}/related", response_model=List[RecommendedItem])
def get_related_recommendations(
    item_id: int,
    limit: int = 4,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve related items computed using MAX semantic cosine similarity and shared tags."""
    target_item = db.query(Item).filter(Item.id == item_id).first()
    if not target_item:
        return []

    engine = RecommendationEngine(db)
    candidates = db.query(Item).filter(
        Item.id != item_id,
        (Item.category_id == target_item.category_id) | (Item.difficulty_level == target_item.difficulty_level)
    ).limit(30).all()

    if not candidates:
        candidates = db.query(Item).filter(Item.id != item_id).limit(30).all()

    ranked = engine.ranker.rank_candidates(current_user, candidates, strategy="hybrid")

    results = []
    for cand_data in ranked[:limit]:
        cand_data["item"]
        explanation = engine.explainer.explain(current_user, cand_data)
        explanation["headline"] = f"Similar to '{target_item.title[:25]}...'"
        explanation["reasons"].insert(0, f"Shares key technical concepts with '{target_item.title}'.")
        enriched = engine._enrich_item(cand_data["item"], current_user)
        results.append(RecommendedItem(
            item=enriched,
            score=cand_data["score"],
            match_percentage=explanation["match_percentage"],
            explanation=explanation
        ))
    return results

@router.get("/status")
def get_ai_pipeline_status():
    """Return runtime diagnostic status of MAX Inference and Mojo Engines."""
    return {
        "project": "RECOMAI",
        "max_engine": max_service.get_status(),
        "mojo_engine": mojo_bridge.get_status(),
        "pipeline_stages": [
            "User Profile & Behavioral State Extraction",
            "Multi-Signal Candidate Generation (Preference, Content, Interaction, Trending)",
            "MAX AI Semantic Embedding & Latent Projection (64-dim)",
            "Mojo High-Performance Vector Cosine Similarity & Matrix Scoring",
            "Mojo SIMD Multi-Factor Candidate Ranking",
            "Transparent Factor-Based Explanation Generation",
            "Client Delivery & Telemetry"
        ]
    }
