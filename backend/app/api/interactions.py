from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.user import User
from app.models.item import Item
from app.models.interaction import Interaction, Rating, Favorite
from app.schemas.interaction import (
    InteractionCreate, InteractionResponse,
    RatingCreate, RatingResponse,
    FavoriteToggle, FavoriteResponse
)
from app.schemas.item import ItemResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/interactions", tags=["User Interactions"])

@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
def record_interaction(
    data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record an interaction (view, dwell time, dislike, hide) to adjust recommendation weights."""
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    interaction = Interaction(
        user_id=current_user.id,
        item_id=data.item_id,
        interaction_type=data.interaction_type,
        dwell_time_seconds=data.dwell_time_seconds or 0.0
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

@router.post("/like/{item_id}", response_model=dict)
def toggle_like(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a like for an item. Updates item likes_count and records interaction."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    existing_like = db.query(Interaction).filter(
        Interaction.user_id == current_user.id,
        Interaction.item_id == item_id,
        Interaction.interaction_type == "like"
    ).first()

    if existing_like:
        db.delete(existing_like)
        item.likes_count = max(0, item.likes_count - 1)
        is_liked = False
        message = "Item unliked"
    else:
        new_like = Interaction(
            user_id=current_user.id,
            item_id=item_id,
            interaction_type="like",
            dwell_time_seconds=0.0
        )
        db.add(new_like)
        item.likes_count += 1
        is_liked = True
        message = "Item liked"

    db.commit()
    return {"item_id": item_id, "is_liked": is_liked, "likes_count": item.likes_count, "message": message}

@router.post("/rate", response_model=RatingResponse)
def submit_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit or update a 1-5 star rating for an item. Dynamically updates item rating_avg."""
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.item_id == data.item_id
    ).first()

    if rating:
        rating.score = data.score
        rating.review = data.review
    else:
        rating = Rating(
            user_id=current_user.id,
            item_id=data.item_id,
            score=data.score,
            review=data.review
        )
        db.add(rating)

    db.flush()

    # Recalculate average rating
    stats = db.query(
        func.avg(Rating.score).label("avg_score"),
        func.count(Rating.id).label("count")
    ).filter(Rating.item_id == data.item_id).first()

    item.rating_avg = round(float(stats.avg_score or 0.0), 2)
    item.rating_count = int(stats.count or 0)

    db.commit()
    db.refresh(rating)
    return rating

@router.post("/favorite/{item_id}", response_model=FavoriteResponse)
def toggle_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle saving an item to favorites."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.item_id == item_id
    ).first()

    if favorite:
        db.delete(favorite)
        db.commit()
        return FavoriteResponse(item_id=item_id, is_favorited=False, message="Removed from favorites")
    else:
        new_fav = Favorite(user_id=current_user.id, item_id=item_id)
        db.add(new_fav)
        db.commit()
        return FavoriteResponse(item_id=item_id, is_favorited=True, message="Added to favorites")

@router.get("/favorites", response_model=List[ItemResponse])
def get_user_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all items favorited by the current user."""
    favs = db.query(Favorite).filter(Favorite.user_id == current_user.id).order_by(Favorite.created_at.desc()).all()
    results = []
    for f in favs:
        item = f.item
        if item:
            is_liked = bool(db.query(Interaction).filter(
                Interaction.user_id == current_user.id,
                Interaction.item_id == item.id,
                Interaction.interaction_type == "like"
            ).first())
            results.append(ItemResponse(
                id=item.id,
                title=item.title,
                slug=item.slug,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
                category_icon=item.category.icon if item.category else None,
                description=item.description,
                content=item.content,
                tags=item.tags or [],
                image_url=item.image_url,
                difficulty_level=item.difficulty_level,
                url=item.url,
                rating_avg=item.rating_avg,
                rating_count=item.rating_count,
                views_count=item.views_count,
                likes_count=item.likes_count,
                created_at=item.created_at,
                updated_at=item.updated_at,
                is_liked=is_liked,
                is_favorited=True
            ))
    return results
