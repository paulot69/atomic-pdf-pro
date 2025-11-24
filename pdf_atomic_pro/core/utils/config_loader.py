import yaml
from pathlib import Path
import logging
from typing import Dict, Any
import os

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
    required_keys = ['structure', 'subtitle_detection', 'templates']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Configuration file is missing required key: '{key}'")
            
    # --- Inject Environment Variables ---
    if os.getenv('SHEET_ID_ATOMICO'):
        config['spreadsheet_id'] = os.getenv('SHEET_ID_ATOMICO')
    
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        config['service_account_file'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

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