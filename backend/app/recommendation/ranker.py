import logging
from typing import List, Dict, Any, Optional
from app.models.user import User
from app.models.item import Item
from app.ai.max_service import max_service
from app.ai.embeddings import get_item_embedding
from app.mojo.bridge import mojo_bridge

logger = logging.getLogger("recomai.ranker")

class RecommendationRanker:
    """Ranks candidates using MAX embeddings for semantic representation and Mojo for vector similarity."""

    def __init__(self):
        self.max_service = max_service
        self.mojo_bridge = mojo_bridge

    def build_user_profile_vector(self, user: User) -> List[float]:
        """Build a semantic embedding of the user's combined profile."""
        profile_parts = []
        if user.preferences:
            if user.preferences.preferred_categories:
                profile_parts.append(" ".join(user.preferences.preferred_categories))
            if user.preferences.preferred_tags:
                profile_parts.append(" ".join(user.preferences.preferred_tags))
            if user.preferences.experience_level:
                profile_parts.append(user.preferences.experience_level)
            if user.preferences.bio:
                profile_parts.append(user.preferences.bio)

        profile_text = " ".join(profile_parts) if profile_parts else "computer science programming technology"
        return self.max_service.generate_embedding(profile_text)

    def rank_candidates(
        self,
        user: Optional[User],
        candidates: List[Item],
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """Rank candidates by evaluating multi-signal features via MAX and Mojo."""
        if not candidates:
            return []

        # 1. User profile vector via MAX
        if user:
            user_vec = self.build_user_profile_vector(user)
            user_prefs = user.preferences
            preferred_cats = [str(c).lower() for c in (user_prefs.preferred_categories if user_prefs else [])]
            preferred_tags = [str(t).lower() for t in (user_prefs.preferred_tags if user_prefs else [])]
        else:
            user_vec = self.max_service.generate_embedding("technology machine learning web devops software")
            preferred_cats = []
            preferred_tags = []

        # 2. Extract item vectors and candidate features
        candidate_signals = []
        candidate_vectors = []
        for item in candidates:
            item_vec = get_item_embedding(item)
            candidate_vectors.append(item_vec)

        # 3. Compute vector similarities via Mojo Batch Engine
        similarities = self.mojo_bridge.batch_cosine_similarity(user_vec, candidate_vectors)

        # 4. Build multi-signal feature objects
        for item, sim in zip(candidates, similarities):
            cat_name = (item.category.name.lower() if item.category else "")
            cat_slug = (item.category.slug.lower() if item.category else "")
            cat_match = 1.0 if any(c in cat_name or c in cat_slug for c in preferred_cats) else 0.0

            item_tags = [str(t).lower() for t in (item.tags or [])]
            tag_overlap_count = sum(1 for t in item_tags if any(pt in t or t in pt for pt in preferred_tags))
            tag_overlap_score = min(1.0, tag_overlap_count / max(1, len(preferred_tags))) if preferred_tags else 0.3

            rating_score = (item.rating_avg / 5.0) if item.rating_avg else 0.5
            popularity_score = min(1.0, (item.views_count * 0.05 + item.likes_count * 0.1))

            candidate_signals.append({
                "item": item,
                "semantic_score": max(0.0, sim),
                "preference_score": (cat_match * 0.6 + tag_overlap_score * 0.4),
                "category_score": cat_match,
                "tag_score": tag_overlap_score,
                "rating_score": rating_score,
                "popularity_score": popularity_score,
            })

        # 5. Define strategy weights
        if strategy == "preference":
            weights = {"semantic": 0.15, "preference": 0.45, "category": 0.15, "tag_overlap": 0.10, "rating": 0.05, "popularity": 0.10}
        elif strategy == "trending":
            weights = {"semantic": 0.15, "preference": 0.10, "category": 0.10, "tag_overlap": 0.05, "rating": 0.50, "popularity": 0.10}
        else:  # hybrid / default
            weights = {"semantic": 0.30, "preference": 0.25, "category": 0.15, "tag_overlap": 0.15, "rating": 0.10, "popularity": 0.05}

        # 6. Rank via Mojo Ranking Engine
        ranked_results = self.mojo_bridge.rank_candidates(candidate_signals, weights)

        # Structure final ranked list
        final_list = []
        for cand, score in ranked_results:
            final_list.append({
                "item": cand["item"],
                "score": score,
                "semantic_score": cand["semantic_score"],
                "preference_score": cand["preference_score"],
                "category_score": cand["category_score"],
                "tag_score": cand["tag_score"],
                "rating_score": cand["rating_score"],
                "popularity_score": cand["popularity_score"],
                "weights": weights,
                "strategy": strategy
            })

        return final_list

recommendation_ranker = RecommendationRanker()
