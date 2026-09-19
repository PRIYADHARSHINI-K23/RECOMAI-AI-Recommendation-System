import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.item import Item
from app.models.recommendation import RecommendationLog
from app.models.interaction import Interaction, Favorite, Rating
from app.recommendation.candidate_gen import CandidateGenerator
from app.recommendation.ranker import recommendation_ranker
from app.recommendation.explainer import recommendation_explainer
from app.schemas.item import ItemResponse

logger = logging.getLogger("recomai.engine")

class RecommendationEngine:
    """Master Recommendation Engine for RECOMAI.
    
    Orchestrates candidate generation, MAX semantic inference, Mojo similarity
    and candidate ranking, and transparent explanation generation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.candidate_gen = CandidateGenerator(db)
        self.ranker = recommendation_ranker
        self.explainer = recommendation_explainer

    def _enrich_item(self, item: Item, user: Optional[User]) -> Dict[str, Any]:
        """Convert an Item model to dict with user-specific flags (liked, favorited, user_rating)."""
        is_liked = False
        is_favorited = False
        user_rating = None

        if user:
            # Check like
            like_exists = self.db.query(Interaction).filter(
                Interaction.user_id == user.id,
                Interaction.item_id == item.id,
                Interaction.interaction_type == "like"
            ).first()
            is_liked = bool(like_exists)

            # Check favorite
            fav_exists = self.db.query(Favorite).filter(
                Favorite.user_id == user.id,
                Favorite.item_id == item.id
            ).first()
            is_favorited = bool(fav_exists)

            # Check rating
            rate_obj = self.db.query(Rating).filter(
                Rating.user_id == user.id,
                Rating.item_id == item.id
            ).first()
            if rate_obj:
                user_rating = rate_obj.score

        return {
            "id": item.id,
            "title": item.title,
            "slug": item.slug,
            "category_id": item.category_id,
            "category_name": item.category.name if item.category else None,
            "category_icon": item.category.icon if item.category else None,
            "description": item.description,
            "content": item.content,
            "tags": item.tags or [],
            "image_url": item.image_url,
            "difficulty_level": item.difficulty_level,
            "url": item.url,
            "rating_avg": item.rating_avg,
            "rating_count": item.rating_count,
            "views_count": item.views_count,
            "likes_count": item.likes_count,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "is_liked": is_liked,
            "is_favorited": is_favorited,
            "user_rating": user_rating
        }

    def get_personalized_recommendations(
        self,
        user: Optional[User],
        limit: int = 10,
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for the user using the full multi-signal pipeline."""
        if user:
            # 1. Candidate generation
            candidates = self.candidate_gen.generate_interaction_candidates(user, limit=limit * 3)
            if len(candidates) < limit:
                more = self.candidate_gen.generate_preference_candidates(user, limit=limit * 2)
                cand_ids = {c.id for c in candidates}
                for m in more:
                    if m.id not in cand_ids:
                        candidates.append(m)
        else:
            candidates = self.candidate_gen.generate_trending_candidates(limit=limit * 2)

        if not candidates:
            # Fallback to all items if dataset is small
            candidates = self.db.query(Item).limit(limit * 2).all()

        # 2. Ranking via MAX Embeddings + Mojo Sim
        ranked_candidates = self.ranker.rank_candidates(user, candidates, strategy=strategy)

        # 3. Formulate output with Explanations
        output = []
        for cand_data in ranked_candidates[:limit]:
            item = cand_data["item"]
            explanation = self.explainer.explain(user, cand_data)
            enriched_item = self._enrich_item(item, user)

            output.append({
                "item": enriched_item,
                "score": cand_data["score"],
                "match_percentage": explanation["match_percentage"],
                "explanation": explanation
            })

            # 4. Optional recommendation logging for analytics
            if user:
                try:
                    log = RecommendationLog(
                        user_id=user.id,
                        item_id=item.id,
                        score=cand_data["score"],
                        match_percentage=explanation["match_percentage"],
                        explanation=explanation["headline"],
                        strategy=strategy
                    )
                    self.db.add(log)
                except Exception:
                    pass

        if user:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        return output

    def get_trending_recommendations(self, user: Optional[User], limit: int = 8) -> List[Dict[str, Any]]:
        """Generate trending / popular recommendations."""
        candidates = self.candidate_gen.generate_trending_candidates(limit=limit * 2)
        ranked = self.ranker.rank_candidates(user, candidates, strategy="trending")

        output = []
        for cand_data in ranked[:limit]:
            explanation = self.explainer.explain(user, cand_data)
            enriched_item = self._enrich_item(cand_data["item"], user)
            output.append({
                "item": enriched_item,
                "score": cand_data["score"],
                "match_percentage": explanation["match_percentage"],
                "explanation": explanation
            })
        return output

    def get_interest_based_recommendations(self, user: User, limit: int = 8) -> List[Dict[str, Any]]:
        """Generate recommendations strictly tailored to the user's selected interests."""
        candidates = self.candidate_gen.generate_preference_candidates(user, limit=limit * 2)
        ranked = self.ranker.rank_candidates(user, candidates, strategy="preference")

        output = []
        for cand_data in ranked[:limit]:
            explanation = self.explainer.explain(user, cand_data)
            enriched_item = self._enrich_item(cand_data["item"], user)
            output.append({
                "item": enriched_item,
                "score": cand_data["score"],
                "match_percentage": explanation["match_percentage"],
                "explanation": explanation
            })
        return output

    def get_recently_viewed(self, user: User, limit: int = 6) -> List[Dict[str, Any]]:
        """Get the items the user recently viewed."""
        views = self.db.query(Interaction).filter(
            Interaction.user_id == user.id,
            Interaction.interaction_type == "view"
        ).order_by(Interaction.created_at.desc()).limit(limit * 2).all()

        seen_ids = set()
        items = []
        for v in views:
            if v.item_id not in seen_ids and v.item:
                seen_ids.add(v.item_id)
                items.append(self._enrich_item(v.item, user))
            if len(items) >= limit:
                break
        return items
