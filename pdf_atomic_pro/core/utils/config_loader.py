import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config():
    """
    Carga la configuración combinando settings.json y variables de entorno.
    Las variables de entorno tienen prioridad.
    """
    # 1. Cargar .env
    # Se asume que el .env está en llaves/.env o en la raíz
    env_path = Path("llaves/.env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv() # Intenta cargar .env por defecto

    # 2. Cargar settings.json
    config = {}
    settings_path = Path("config/settings.json")
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"No se pudo cargar settings.json: {e}")

    # 3. Combinar/Override con Env Vars (mapeo explícito para claves clave)

    # Rutas
    config['dockerized'] = os.getenv('DOCKERIZED', str(config.get('dockerized', 'false'))).lower() == 'true'
    config['local_input_path'] = os.getenv('LOCAL_INPUT_PATH', config.get('local_input_path', ''))
    config['local_output_path'] = os.getenv('LOCAL_OUTPUT_PATH', config.get('local_output_path', './Libros Atomicos'))

    config['docker_input_path_prefix'] = os.getenv('DOCKER_INPUT_PATH_PREFIX', config.get('docker_input_path_prefix', '/input'))
    config['docker_output_path'] = os.getenv('DOCKER_OUTPUT_PATH', config.get('docker_output_path', '/output'))

    # Google Sheets
    config['spreadsheet_id'] = os.getenv('SHEET_ID_ATOMICO', os.getenv('SPREADSHEET_ID', config.get('spreadsheet_id', '')))
    config['service_account_file'] = os.getenv('SERVICE_ACCOUNT_FILE', config.get('service_account_file', 'llaves/torre_credentials.json'))

    # Logging
    config['log_level'] = os.getenv('LOG_LEVEL', config.get('log_level', 'INFO'))

    # UI
    config['ui_dir'] = os.getenv('UI_DIR', config.get('ui_dir', '/app/pdf_atomic_pro/ui/dist'))

    return config
