import logging
from typing import List, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.item import Item
from app.models.interaction import Interaction, Rating, Favorite

logger = logging.getLogger("recomai.candidate_gen")

class CandidateGenerator:
    """Generates recommendation candidates from multiple behavioral & content signals."""

    def __init__(self, db: Session):
        self.db = db

    def get_excluded_item_ids(self, user_id: Optional[int]) -> Set[int]:
        """Get IDs of items that the user explicitly hid or disliked."""
        if not user_id:
            return set()
        
        disliked_or_hidden = self.db.query(Interaction.item_id).filter(
            Interaction.user_id == user_id,
            Interaction.interaction_type.in_(["dislike", "hide"])
        ).all()
        
        return {row[0] for row in disliked_or_hidden}

    def get_consumed_item_ids(self, user_id: Optional[int]) -> Set[int]:
        """Get IDs of items the user has already viewed or interacted with."""
        if not user_id:
            return set()
        
        viewed = self.db.query(Interaction.item_id).filter(
            Interaction.user_id == user_id,
            Interaction.interaction_type == "view"
        ).all()
        return {row[0] for row in viewed}

    def generate_preference_candidates(self, user: User, limit: int = 30) -> List[Item]:
        """Generate candidates based on user's onboarded preferences (categories & tags)."""
        excluded = self.get_excluded_item_ids(user.id)
        prefs = user.preferences

        if not prefs or (not prefs.preferred_categories and not prefs.preferred_tags):
            return self.generate_trending_candidates(limit=limit, exclude_ids=excluded)

        query = self.db.query(Item)
        if excluded:
            query = query.filter(~Item.id.in_(excluded))

        all_items = query.all()
        scored_items = []

        preferred_cats = [str(c).lower() for c in (prefs.preferred_categories or [])]
        preferred_tags = [str(t).lower() for t in (prefs.preferred_tags or [])]

        for item in all_items:
            cat_name = (item.category.name.lower() if item.category else "")
            cat_slug = (item.category.slug.lower() if item.category else "")
            
            cat_match = any(c in cat_name or c in cat_slug for c in preferred_cats)
            item_tags = [str(t).lower() for t in (item.tags or [])]
            tag_overlap = sum(1 for t in item_tags if any(pt in t or t in pt for pt in preferred_tags))

            if cat_match or tag_overlap > 0:
                relevance = (2.0 if cat_match else 0.0) + (tag_overlap * 1.5) + (item.rating_avg * 0.2)
                scored_items.append((item, relevance))

        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored_items[:limit]]

    def generate_interaction_candidates(self, user: User, limit: int = 30) -> List[Item]:
        """Generate candidates based on items the user previously liked, favorited, or rated high."""
        excluded = self.get_excluded_item_ids(user.id)

        # Find items the user liked, favorited, or rated >= 4
        liked_ids = {row[0] for row in self.db.query(Interaction.item_id).filter(
            Interaction.user_id == user.id, Interaction.interaction_type == "like"
        ).all()}

        fav_ids = {row[0] for row in self.db.query(Favorite.item_id).filter(
            Favorite.user_id == user.id
        ).all()}

        high_rated_ids = {row[0] for row in self.db.query(Rating.item_id).filter(
            Rating.user_id == user.id, Rating.score >= 4.0
        ).all()}

        seed_item_ids = liked_ids | fav_ids | high_rated_ids
        if not seed_item_ids:
            return self.generate_preference_candidates(user, limit=limit)

        seed_items = self.db.query(Item).filter(Item.id.in_(seed_item_ids)).all()
        seed_categories = {item.category_id for item in seed_items}
        seed_tags = set()
        for item in seed_items:
            seed_tags.update([t.lower() for t in (item.tags or [])])

        candidate_query = self.db.query(Item).filter(
            ~Item.id.in_(seed_item_ids | excluded)
        )
        candidates = candidate_query.all()

        scored = []
        for cand in candidates:
            cat_score = 2.0 if cand.category_id in seed_categories else 0.0
            cand_tags = [t.lower() for t in (cand.tags or [])]
            tag_overlap = sum(1 for t in cand_tags if t in seed_tags)
            score = cat_score + (tag_overlap * 1.2) + (cand.rating_avg * 0.3)
            if score > 0:
                scored.append((cand, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]

    def generate_trending_candidates(self, limit: int = 30, exclude_ids: Optional[Set[int]] = None) -> List[Item]:
        """Generate candidates by combining high view counts, likes, and ratings."""
        query = self.db.query(Item)
        if exclude_ids:
            query = query.filter(~Item.id.in_(exclude_ids))

        # Popularity score = (views * 0.4) + (likes * 1.5) + (rating_avg * rating_count * 0.8)
        items = query.all()
        scored = []
        for item in items:
            pop_score = (item.views_count * 0.4) + (item.likes_count * 1.5) + (item.rating_avg * (item.rating_count + 1) * 0.5)
            scored.append((item, pop_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]
