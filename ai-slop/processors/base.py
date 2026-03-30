"""Abstract base class for data processors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from schema import Item, ProcessedItem


class DataProcessor(ABC):
    """Abstract base class for all data processors."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        self.config = config
        self.processor_type = self.__class__.__name__

    @abstractmethod
    def process(self, items: List[Item]) -> List[ProcessedItem]:
        """
        Process a list of items.
        
        Args:
            items: List of Item objects to process
            
        Returns:
            List of ProcessedItem objects
        """
        pass

    def process_single(self, item: Item) -> ProcessedItem:
        """
        Process a single item.
        
        Args:
            item: Item to process
            
        Returns:
            ProcessedItem object
        """
        return self.process([item])[0]
