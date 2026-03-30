"""
New modular pipeline entry point.
Usage: python main_pipeline.py --config configs/arxiv_digest.yaml
"""

import argparse
import logging
import sys

from pipeline import Pipeline


def setup_logging(level=logging.INFO):
    """Configure logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Run a content generation pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/arxiv_digest.yaml",
        help="Path to pipeline configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Loading pipeline configuration: {args.config}")
        pipeline = Pipeline(args.config)
        
        logger.info("Starting pipeline execution...")
        results = pipeline.run()
        
        logger.info(f"Pipeline completed with {len(results)} results")
        
        # Print summary
        success_count = sum(1 for r in results if r.success)
        logger.info(f"✓ {success_count} successful, ✗ {len(results) - success_count} failed")
        
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
