import logging
import os
from pathlib import Path

# Update default log path to reflect new structure: pdf_atomic_pro/logs/app.log
# We use a path relative to the package root if possible, or relative to CWD.
# Assuming running from root, 'pdf_atomic_pro/logs/app.log' is correct.
DEFAULT_LOG_FILE = "pdf_atomic_pro/logs/app.log"

def setup_logging(log_level="INFO", log_file=DEFAULT_LOG_FILE):
    """
    Configures logging to file and console.
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized.")
