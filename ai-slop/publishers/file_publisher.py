"""File-based content publisher."""

import os
from typing import Any, Dict

from schema import GeneratedContent, PublishResult
from publishers.base import ContentPublisher


class FilePublisher(ContentPublisher):
    """Publish content to local files."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.output_dir = config.get("output_dir", "output")
        self.formats = config.get("formats", ["md", "html"])
        os.makedirs(self.output_dir, exist_ok=True)

    def validate(self) -> bool:
        """Validate publisher configuration."""
        if not os.path.isdir(self.output_dir):
            raise ValueError(f"Output directory does not exist: {self.output_dir}")
        return True

    def publish(self, generated_content: GeneratedContent) -> PublishResult:
        """Publish content to file."""
        try:
            item = generated_content.processed_item.item
            filename = f"{item.source_id}_{generated_content.content_type}"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(generated_content.content)
            
            return PublishResult(
                generated_content=generated_content,
                publisher_type=self.publisher_type,
                success=True,
                message=f"Published to {filepath}",
                publish_url=filepath,
            )
        except Exception as e:
            return PublishResult(
                generated_content=generated_content,
                publisher_type=self.publisher_type,
                success=False,
                message=f"Error publishing: {str(e)}",
            )
