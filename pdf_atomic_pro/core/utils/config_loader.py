import yaml
from pathlib import Path
import logging
from typing import Dict, Any
import os

# Resolves to config/rules.yaml relative to this file
# This file is in pdf_atomic_pro/core/utils/
# So parents[2] is the package root (pdf_atomic_pro/).
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config/rules.yaml"

def load_config(config_path: Path = None) -> Dict[str, Any]:
    """
    Loads, validates, and returns the configuration from the YAML file.

    Args:
        config_path: The path to the configuration YAML file. Defaults to DEFAULT_CONFIG_PATH.

    Returns:
        A dictionary containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        ValueError: If the configuration file is invalid or missing essential keys.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        # Fallback to settings.json if rules.yaml doesn't exist (legacy support)
        settings_path = config_path.parent / "settings.json"
        if settings_path.exists():
            logging.info(f"rules.yaml not found, falling back to {settings_path}")
            config_path = settings_path
        else:
             # If neither exists, raise error or return defaults if strictness isn't required.
             # However, for now we will raise error as per docstring.
             raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse configuration file: {e}")

    # Required keys validation (soft validation for now to avoid breaking legacy configs)
    required_keys = ['structure', 'templates']
    for key in required_keys:
        if key not in config:
            # logging.warning(f"Configuration file is missing key: '{key}'. Using defaults or expecting errors.")
            pass
            
    # --- Inject Environment Variables ---
    if os.getenv('SHEET_ID_ATOMICO'):
        config['spreadsheet_id'] = os.getenv('SHEET_ID_ATOMICO')
    
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        config['service_account_file'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    if os.getenv('LOG_LEVEL'):
        config['log_level'] = os.getenv('LOG_LEVEL')

    # logging.info(f"Configuration loaded from {config_path}")
    return config

if __name__ == '__main__':
    # Example of how to load the configuration
    try:
        config = load_config()
        import pprint
        pprint.pprint(config)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
