from typing import Dict, Any, List, Optional
from app.models.user import User
from app.models.item import Item

class RecommendationExplainer:
    """Generates transparent, mathematically grounded explanations for why an item was recommended."""

    def explain(
        self,
        user: Optional[User],
        candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        item: Item = candidate_data["item"]
        score: float = candidate_data["score"]
        strategy: str = candidate_data.get("strategy", "hybrid")
        
        sem_score = candidate_data.get("semantic_score", 0.0)
        pref_score = candidate_data.get("preference_score", 0.0)
        cat_score = candidate_data.get("category_score", 0.0)
        tag_score = candidate_data.get("tag_score", 0.0)
        rat_score = candidate_data.get("rating_score", 0.0)
        pop_score = candidate_data.get("popularity_score", 0.0)

        # Scale score to a natural match percentage (e.g. 70% to 98%)
        # Base between 65 and 99
        match_percentage = int(min(99, max(65, round(score * 100))))

        reasons: List[str] = []
        user_prefs = user.preferences if user else None
        preferred_cats = [str(c).lower() for c in (user_prefs.preferred_categories if user_prefs else [])]
        preferred_tags = [str(t).lower() for t in (user_prefs.preferred_tags if user_prefs else [])]

        # 1. Check category alignment
        cat_name = item.category.name if item.category else ""
        if cat_score > 0.5 and cat_name:
            reasons.append(f"Directly aligns with your selected interest in {cat_name}.")

        # 2. Check tag matches
        matching_tags = []
        for t in (item.tags or []):
            if any(pt in t.lower() or t.lower() in pt for pt in preferred_tags):
                matching_tags.append(t)
        if matching_tags:
            tag_list_str = ", ".join(f"'{t}'" for t in matching_tags[:3])
            reasons.append(f"Matches your topic preferences: {tag_list_str}.")

        # 3. Check semantic similarity
        if sem_score >= 0.70:
            reasons.append("Semantic similarity to your profile based on content analysis.")
        elif sem_score >= 0.50:
            reasons.append("Semantically related to topics in your recent learning activity.")

        # 4. Check rating and community sentiment
        if item.rating_avg >= 4.5:
            reasons.append(f"Highly rated by learners ({item.rating_avg:.1f}★ with {item.rating_count} reviews).")
        elif item.rating_avg >= 4.0:
            reasons.append(f"Strong community rating: {item.rating_avg:.1f}★.")

        # 5. Check popularity/velocity
        if pop_score > 0.4:
            reasons.append("Trending among learners with similar engineering interests.")

        # Fallback reason if cold-start or low signals
        if not reasons:
            reasons.append(f"Recommended resource in {cat_name or 'Computer Science'}.")

        # Determine best headline
        if matching_tags:
            headline = f"Matches your {' & '.join(matching_tags[:2])} interests"
        elif cat_score > 0.5:
            headline = f"Matches your interest in {cat_name}"
        elif sem_score > 0.65:
            headline = "Semantically aligned with your learning profile"
        elif item.rating_avg >= 4.5:
            headline = f"Top-rated {cat_name} resource"
        else:
            headline = "Recommended based on community engagement"

        return {
            "match_percentage": match_percentage,
            "score": round(score, 4),
            "headline": headline,
            "reasons": reasons,
            "factor_weights": {
                "Semantic Similarity": round(sem_score, 2),
                "Category Match": round(cat_score, 2),
                "Tag Preferences": round(tag_score, 2),
                "Rating & Quality": round(rat_score, 2),
                "Popularity": round(pop_score, 2)
            },
            "strategy": strategy
        }

recommendation_explainer = RecommendationExplainer()
