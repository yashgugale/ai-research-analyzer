"""Abstract base class for data sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from schema import Item


class DataSource(ABC):
    """Abstract base class for all data sources."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data source.
        
        Args:
            config: Configuration dictionary for the source
        """
        self.config = config
        self.source_type = self.__class__.__name__

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch raw data from the source.
        
        Returns:
            List of raw items (dictionaries)
        """
        pass

    @abstractmethod
    def parse(self, raw_item: Dict[str, Any]) -> Item:
        """
        Parse a raw item into a unified Item schema.
        
        Args:
            raw_item: Raw item from fetch()
            
        Returns:
            Parsed Item object
        """
        pass

    @abstractmethod
    def cache_key(self, raw_item: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for an item.
        
        Args:
            raw_item: Raw item from fetch()
            
        Returns:
            Unique string identifier
        """
        pass

    def fetch_and_parse(self) -> List[Item]:
        """
        Fetch and parse all items from the source.
        
        Returns:
            List of parsed Item objects
        """
        raw_items = self.fetch()
        return [self.parse(item) for item in raw_items]
