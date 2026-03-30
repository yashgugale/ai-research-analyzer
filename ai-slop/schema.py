"""
Unified data models for the content pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Item:
    """Raw item fetched from a source."""

    source_type: str
    source_id: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "fetched_at": self.fetched_at.isoformat(),
        }


@dataclass
class ProcessedItem:
    """Item after processing (ranking, filtering, deduplication)."""

    item: Item
    score: float = 0.0
    rank: int = 0
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item": self.item.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "processing_metadata": self.processing_metadata,
            "processed_at": self.processed_at.isoformat(),
        }


@dataclass
class GeneratedContent:
    """Content generated from processed items."""

    processed_item: ProcessedItem
    content_type: str  # "markdown", "html", "json", etc.
    content: str
    template_name: str
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processed_item": self.processed_item.to_dict(),
            "content_type": self.content_type,
            "content": self.content,
            "template_name": self.template_name,
            "generation_metadata": self.generation_metadata,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class PublishResult:
    """Result of publishing content."""

    generated_content: GeneratedContent
    publisher_type: str
    success: bool
    message: str
    publish_url: Optional[str] = None
    publish_metadata: Dict[str, Any] = field(default_factory=dict)
    published_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_content": self.generated_content.to_dict(),
            "publisher_type": self.publisher_type,
            "success": self.success,
            "message": self.message,
            "publish_url": self.publish_url,
            "publish_metadata": self.publish_metadata,
            "published_at": self.published_at.isoformat(),
        }
