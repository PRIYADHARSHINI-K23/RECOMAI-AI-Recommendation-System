from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserPreferences
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserPreferencesSchema, Token
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account with initial preferences."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )

    # Hash password securely
    hashed_pw = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=user_in.role if user_in.role in ("user", "admin") else "user",
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Create initial user preferences
    prefs = UserPreferences(
        user_id=new_user.id,
        preferred_categories=user_in.preferred_categories or [],
        preferred_tags=user_in.preferred_tags or [],
        experience_level=user_in.experience_level or "Intermediate"
    )
    db.add(prefs)
    db.commit()
    db.refresh(new_user)

    # Generate JWT access token
    access_token = create_access_token(
        data={"sub": new_user.email, "role": new_user.role, "id": new_user.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning JWT token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current logged-in user profile."""
    return current_user

@router.put("/preferences", response_model=UserResponse)
def update_preferences(
    prefs_in: UserPreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user category and topic preferences (e.g. from onboarding or profile)."""
    prefs = current_user.preferences
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.preferred_categories = prefs_in.preferred_categories
    prefs.preferred_tags = prefs_in.preferred_tags
    prefs.experience_level = prefs_in.experience_level
    if prefs_in.bio is not None:
        prefs.bio = prefs_in.bio

    db.commit()
    db.refresh(current_user)
    return current_user
