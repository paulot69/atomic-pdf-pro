import yaml
from pathlib import Path
import logging
from typing import Dict, Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config/rules.yaml"

def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Loads, validates, and returns the configuration from the YAML file.

    Args:
        config_path: The path to the configuration YAML file. Defaults to the standard location.

    Returns:
        A dictionary containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        ValueError: If the configuration file is invalid or missing essential keys.
    """
    logging.info(f"Loading configuration from: {config_path}")
    if not config_path.is_file():
        logging.error(f"Configuration file not found at: {config_path}")
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        raise ValueError(f"Error parsing configuration file: {e}")

    # --- Validation ---
    if not config:
        raise ValueError("Configuration file is empty or invalid.")

    required_keys = ['structure', 'subtitle_detection', 'templates']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Configuration file is missing required key: '{key}'")
            
    logging.info("Configuration loaded and validated successfully.")
    return config

if __name__ == '__main__':
    # Example of how to load the configuration
    try:
        config = load_config()
        import pprint
        pprint.pprint(config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to load configuration: {e}")