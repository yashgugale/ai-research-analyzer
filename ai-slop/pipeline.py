"""Core pipeline orchestrator for content generation."""

import logging
from typing import Any, Dict, List, Type

from config_loader import ConfigLoader
from schema import Item, ProcessedItem, GeneratedContent, PublishResult
from sources.base import DataSource
from processors.base import DataProcessor
from generators.base import ContentGenerator
from publishers.base import ContentPublisher


logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline orchestrator that coordinates all components."""

    def __init__(self, config_path: str):
        """
        Initialize pipeline from configuration file.
        
        Args:
            config_path: Path to YAML/JSON configuration file
        """
        self.config = ConfigLoader.load(config_path)
        self.pipeline_name = self.config.get("pipeline", {}).get("name", "Unnamed Pipeline")
        
        self.sources: List[DataSource] = []
        self.processors: List[DataProcessor] = []
        self.generators: List[ContentGenerator] = []
        self.publishers: List[ContentPublisher] = []
        
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize all pipeline components from configuration."""
        logger.info(f"Initializing pipeline: {self.pipeline_name}")
        
        # Initialize sources
        sources_config = self.config.get("sources", [])
        for source_config in sources_config:
            source = self._create_component(source_config, "sources", DataSource)
            if source:
                self.sources.append(source)
                logger.info(f"  ✓ Initialized source: {source.source_type}")

        # Initialize processors
        processors_config = self.config.get("processors", [])
        for processor_config in processors_config:
            processor = self._create_component(processor_config, "processors", DataProcessor)
            if processor:
                self.processors.append(processor)
                logger.info(f"  ✓ Initialized processor: {processor.processor_type}")

        # Initialize generators
        generators_config = self.config.get("generators", [])
        for generator_config in generators_config:
            generator = self._create_component(generator_config, "generators", ContentGenerator)
            if generator:
                self.generators.append(generator)
                logger.info(f"  ✓ Initialized generator: {generator.generator_type}")

        # Initialize publishers
        publishers_config = self.config.get("publishers", [])
        for publisher_config in publishers_config:
            publisher = self._create_component(publisher_config, "publishers", ContentPublisher)
            if publisher:
                try:
                    publisher.validate()
                    self.publishers.append(publisher)
                    logger.info(f"  ✓ Initialized publisher: {publisher.publisher_type}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to validate publisher: {e}")

    def _create_component(
        self,
        component_config: Dict[str, Any],
        component_type: str,
        base_class: Type,
    ) -> Any:
        """
        Dynamically create a component from configuration.
        
        Args:
            component_config: Component configuration dictionary
            component_type: Type of component ("sources", "processors", etc.)
            base_class: Base class for the component
            
        Returns:
            Initialized component instance or None if creation fails
        """
        try:
            component_name = component_config.get("type")
            if not component_name:
                logger.error(f"Component config missing 'type' field: {component_config}")
                return None

            # Convert component name to class name (e.g., "arxiv_source" -> "ArxivSource")
            class_name = "".join(word.capitalize() for word in component_name.split("_"))
            
            # Import the module
            module_name = f"{component_type}.{component_name}"
            try:
                module = __import__(module_name, fromlist=[class_name])
                component_class = getattr(module, class_name)
                
                # Instantiate with config
                config = component_config.get("config", {})
                return component_class(config)
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load component {class_name} from {module_name}: {e}")
                return None

        except Exception as e:
            logger.error(f"Error creating component: {e}")
            return None

    def run(self) -> List[PublishResult]:
        """
        Execute the complete pipeline.
        
        Returns:
            List of PublishResult objects
        """
        logger.info(f"Starting pipeline execution: {self.pipeline_name}")
        
        # Step 1: Fetch items from all sources
        logger.info("Step 1: Fetching items from sources...")
        items = self._fetch_items()
        logger.info(f"  Fetched {len(items)} items")

        # Step 2: Process items through all processors
        logger.info("Step 2: Processing items...")
        processed_items = self._process_items(items)
        logger.info(f"  Processed {len(processed_items)} items")

        # Step 3: Generate content from processed items
        logger.info("Step 3: Generating content...")
        generated_contents = self._generate_content(processed_items)
        logger.info(f"  Generated {len(generated_contents)} content pieces")

        # Step 4: Publish generated content
        logger.info("Step 4: Publishing content...")
        publish_results = self._publish_content(generated_contents)
        logger.info(f"  Published {len(publish_results)} items")

        logger.info(f"Pipeline execution complete: {self.pipeline_name}")
        return publish_results

    def _fetch_items(self) -> List[Item]:
        """Fetch items from all sources."""
        items = []
        for source in self.sources:
            try:
                source_items = source.fetch_and_parse()
                items.extend(source_items)
                logger.debug(f"  {source.source_type}: fetched {len(source_items)} items")
            except Exception as e:
                logger.error(f"  Error fetching from {source.source_type}: {e}")
        return items

    def _process_items(self, items: List[Item]) -> List[ProcessedItem]:
        """Process items through all processors."""
        processed_items = [ProcessedItem(item=item) for item in items]
        
        for processor in self.processors:
            try:
                processed_items = processor.process(processed_items)
                logger.debug(f"  {processor.processor_type}: processed {len(processed_items)} items")
            except Exception as e:
                logger.error(f"  Error processing with {processor.processor_type}: {e}")
        
        return processed_items

    def _generate_content(self, processed_items: List[ProcessedItem]) -> List[GeneratedContent]:
        """Generate content from processed items."""
        generated_contents = []
        
        for generator in self.generators:
            try:
                for processed_item in processed_items:
                    content = generator.generate(processed_item)
                    generated_contents.append(content)
                logger.debug(f"  {generator.generator_type}: generated {len(processed_items)} content pieces")
            except Exception as e:
                logger.error(f"  Error generating with {generator.generator_type}: {e}")
        
        return generated_contents

    def _publish_content(self, generated_contents: List[GeneratedContent]) -> List[PublishResult]:
        """Publish generated content to all publishers."""
        results = []
        
        for publisher in self.publishers:
            try:
                for content in generated_contents:
                    result = publisher.publish(content)
                    results.append(result)
                    status = "✓" if result.success else "✗"
                    logger.debug(f"  {status} {publisher.publisher_type}: {result.message}")
            except Exception as e:
                logger.error(f"  Error publishing with {publisher.publisher_type}: {e}")
        
        return results
