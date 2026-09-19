from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database.session import get_db
from app.models.item import Item, Category
from app.models.interaction import Interaction, Favorite, Rating
from app.schemas.item import ItemResponse, CategoryResponse
from app.auth.dependencies import get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/items", tags=["Items & Categories"])

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Retrieve all categories with their item counts."""
    categories = db.query(Category).order_by(Category.name.asc()).all()
    results = []
    for cat in categories:
        count = db.query(func.count(Item.id)).filter(Item.category_id == cat.id).scalar()
        results.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon,
            created_at=cat.created_at,
            items_count=count or 0
        ))
    return results

@router.get("", response_model=List[ItemResponse])
def get_items(
    category_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    tag: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort_by: str = Query("popular", pattern="^(popular|rating|newest|title)$"),
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve items with filtering by category, tag, difficulty, and sorting."""
    query = db.query(Item)

    if category_id:
        query = query.filter(Item.category_id == category_id)
    elif category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    if difficulty:
        query = query.filter(Item.difficulty_level.ilike(difficulty))

    if sort_by == "popular":
        query = query.order_by(desc(Item.views_count + Item.likes_count * 2))
    elif sort_by == "rating":
        query = query.order_by(desc(Item.rating_avg), desc(Item.rating_count))
    elif sort_by == "newest":
        query = query.order_by(desc(Item.created_at))
    elif sort_by == "title":
        query = query.order_by(Item.title.asc())

    items = query.offset(offset).limit(limit).all()

    results = []
    for item in items:
        # Tag filtering if specified
        if tag:
            item_tags = [t.lower() for t in (item.tags or [])]
            if tag.lower() not in item_tags:
                continue

        is_liked = False
        is_favorited = False
        user_rating = None

        if current_user:
            is_liked = bool(db.query(Interaction).filter(
                Interaction.user_id == current_user.id,
                Interaction.item_id == item.id,
                Interaction.interaction_type == "like"
            ).first())
            is_favorited = bool(db.query(Favorite).filter(
                Favorite.user_id == current_user.id,
                Favorite.item_id == item.id
            ).first())
            rate_obj = db.query(Rating).filter(
                Rating.user_id == current_user.id,
                Rating.item_id == item.id
            ).first()
            if rate_obj:
                user_rating = rate_obj.score

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
            is_favorited=is_favorited,
            user_rating=user_rating
        ))

    return results

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve details of a single item and record view interaction."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Increment item view count
    item.views_count += 1

    # Record view interaction for recommendation signals
    if current_user:
        view_interaction = Interaction(
            user_id=current_user.id,
            item_id=item.id,
            interaction_type="view",
            dwell_time_seconds=10.0
        )
        db.add(view_interaction)

    db.commit()
    db.refresh(item)

    is_liked = False
    is_favorited = False
    user_rating = None

    if current_user:
        is_liked = bool(db.query(Interaction).filter(
            Interaction.user_id == current_user.id,
            Interaction.item_id == item.id,
            Interaction.interaction_type == "like"
        ).first())
        is_favorited = bool(db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.item_id == item.id
        ).first())
        rate_obj = db.query(Rating).filter(
            Rating.user_id == current_user.id,
            Rating.item_id == item.id
        ).first()
        if rate_obj:
            user_rating = rate_obj.score

    return ItemResponse(
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
        is_favorited=is_favorited,
        user_rating=user_rating
    )
