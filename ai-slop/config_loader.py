"""Load and parse YAML/JSON pipeline configurations."""

import json
import os
from typing import Any, Dict

try:
    import yaml
except ImportError:
    yaml = None


class ConfigLoader:
    """Load pipeline configurations from YAML or JSON files."""

    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is not supported
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        _, ext = os.path.splitext(config_path)

        if ext.lower() == ".yaml" or ext.lower() == ".yml":
            if yaml is None:
                raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install pyyaml")
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        elif ext.lower() == ".json":
            with open(config_path, "r") as f:
                return json.load(f)

        else:
            raise ValueError(f"Unsupported configuration file format: {ext}")

    @staticmethod
    def save(config: Dict[str, Any], config_path: str) -> None:
        """
        Save configuration to YAML or JSON file.
        
        Args:
            config: Configuration dictionary
            config_path: Path to save configuration file
        """
        _, ext = os.path.splitext(config_path)

        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)

        if ext.lower() == ".yaml" or ext.lower() == ".yml":
            if yaml is None:
                raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install pyyaml")
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

        elif ext.lower() == ".json":
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

        else:
            raise ValueError(f"Unsupported configuration file format: {ext}")
