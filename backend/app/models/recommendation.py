from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    match_percentage = Column(Integer, nullable=False)
    explanation = Column(String(500), nullable=False)
    strategy = Column(String(50), nullable=False)  # "content", "preference", "interaction", "trending", "hybrid"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="recommendation_logs")
    item = relationship("Item", back_populates="recommendation_logs")
