from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.item import Item
from app.models.interaction import SearchHistory
from app.models.user import User
from app.schemas.recommendation import RecommendedItem
from app.auth.dependencies import get_current_user_optional
from app.ai.max_service import max_service
from app.ai.embeddings import get_item_embedding
from app.mojo.bridge import mojo_bridge
from app.recommendation.engine import RecommendationEngine

router = APIRouter(prefix="/search", tags=["Semantic Search"])

@router.get("", response_model=List[RecommendedItem])
def search_items(
    q: str = Query(..., min_length=1, description="Search query string"),
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = 20,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Semantic & keyword hybrid search powered by MAX embeddings and Mojo similarity."""
    engine = RecommendationEngine(db)
    
    # 1. Fetch candidate items
    query_obj = db.query(Item)
    if category_id:
        query_obj = query_obj.filter(Item.category_id == category_id)
    if difficulty:
        query_obj = query_obj.filter(Item.difficulty_level.ilike(difficulty))

    all_items = query_obj.all()
    if not all_items:
        return []

    # 2. Generate MAX semantic embedding for user query
    query_vec = max_service.generate_embedding(q)

    # 3. Extract candidate embeddings
    candidate_vecs = [get_item_embedding(item) for item in all_items]

    # 4. Compute vector similarities via Mojo Batch Engine
    similarities = mojo_bridge.batch_cosine_similarity(query_vec, candidate_vecs)

    # 5. Hybrid scoring: Combine MAX semantic cosine similarity with keyword match
    q_lower = q.lower().strip()
    q_words = [w for w in q_lower.split() if len(w) > 2]

    scored = []
    for item, sim in zip(all_items, similarities):
        title_lower = item.title.lower()
        desc_lower = item.description.lower()
        tags_lower = [t.lower() for t in (item.tags or [])]

        # Lexical keyword score
        keyword_hits = 0
        for w in q_words:
            if w in title_lower:
                keyword_hits += 2.0
            if any(w in t for t in tags_lower):
                keyword_hits += 1.5
            if w in desc_lower:
                keyword_hits += 0.8
        
        lexical_score = min(1.0, keyword_hits / max(1, len(q_words) * 2))

        # Hybrid composite score: 65% MAX semantic similarity, 35% lexical match
        hybrid_score = (0.65 * max(0.0, sim)) + (0.35 * lexical_score)
        match_pct = int(min(99, max(50, round((hybrid_score * 0.5 + 0.5) * 100))))

        scored.append((item, hybrid_score, match_pct, sim, lexical_score))

    # Sort descending by hybrid score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Filter out low-relevance results
    filtered_results = [x for x in scored if x[1] > 0.15][:limit]
    if not filtered_results and scored:
        filtered_results = scored[:5]

    # 6. Record search query in search_history
    try:
        sh = SearchHistory(
            user_id=current_user.id if current_user else None,
            query=q,
            results_count=len(filtered_results)
        )
        db.add(sh)
        db.commit()
    except Exception:
        db.rollback()

    # 7. Formulate final response with semantic explanation
    results = []
    for item, score, match_pct, sem_sim, lex_score in filtered_results:
        enriched_item = engine._enrich_item(item, current_user)
        
        reasons = []
        if sem_sim > 0.6:
            reasons.append("High semantic affinity with your conceptual query.")
        if lex_score > 0.4:
            reasons.append(f"Directly matches keywords in title and tags.")
        if item.rating_avg >= 4.5:
            reasons.append(f"Top-rated resource: {item.rating_avg}★.")
        if not reasons:
            reasons.append(f"Contextually relevant {item.category.name if item.category else 'tech'} item.")

        explanation = {
            "match_percentage": match_pct,
            "score": round(score, 4),
            "headline": f"Semantically matches '{q}' ({match_pct}% match)",
            "reasons": reasons,
            "factor_weights": {
                "max_semantic_similarity": round(sem_sim, 2),
                "keyword_overlap": round(lex_score, 2),
                "rating": round(item.rating_avg / 5.0, 2)
            },
            "strategy": "semantic_search"
        }

        results.append(RecommendedItem(
            item=enriched_item,
            score=score,
            match_percentage=match_pct,
            explanation=explanation
        ))

    return results
