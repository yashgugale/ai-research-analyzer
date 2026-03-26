"""Abstract base class for content publishers."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from schema import GeneratedContent, PublishResult


class ContentPublisher(ABC):
    """Abstract base class for all content publishers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content publisher.
        
        Args:
            config: Configuration dictionary for the publisher
        """
        self.config = config
        self.publisher_type = self.__class__.__name__

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that the publisher is properly configured.
        
        Returns:
            True if valid, raises exception otherwise
        """
        pass

    @abstractmethod
    def publish(self, generated_content: GeneratedContent) -> PublishResult:
        """
        Publish content to the destination.
        
        Args:
            generated_content: GeneratedContent to publish
            
        Returns:
            PublishResult object
        """
        pass
