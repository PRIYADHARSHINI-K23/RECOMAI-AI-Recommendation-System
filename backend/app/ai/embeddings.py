from typing import List
from app.models.item import Item
from app.ai.max_service import max_service

def build_item_semantic_text(item: Item) -> str:
    """Combine title, category, description, and tags into a rich semantic string for MAX."""
    tags_str = " ".join(item.tags or [])
    cat_str = item.category.name if item.category else ""
    return f"{item.title} {cat_str} {item.description} {tags_str} {item.difficulty_level}"

def get_item_embedding(item: Item) -> List[float]:
    """Retrieve or compute MAX semantic embedding for an Item."""
    text = build_item_semantic_text(item)
    return max_service.generate_embedding(text)
