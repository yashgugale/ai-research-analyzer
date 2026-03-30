"""Abstract base class for content generators."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from schema import ProcessedItem, GeneratedContent


class ContentGenerator(ABC):
    """Abstract base class for all content generators."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content generator.
        
        Args:
            config: Configuration dictionary for the generator
        """
        self.config = config
        self.generator_type = self.__class__.__name__
        self.content_type = config.get("content_type", "text")
        self.template_name = config.get("template", "default")

    @abstractmethod
    def generate(self, processed_item: ProcessedItem) -> GeneratedContent:
        """
        Generate content from a processed item.
        
        Args:
            processed_item: ProcessedItem to generate content from
            
        Returns:
            GeneratedContent object
        """
        pass

    @abstractmethod
    def supports_template(self, template_name: str) -> bool:
        """
        Check if this generator supports a given template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            True if template is supported
        """
        pass
