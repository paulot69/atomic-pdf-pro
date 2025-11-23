import os
import logging
from pdf_atomic_pro.utils.config_loader import load_config

logger = logging.getLogger(__name__)

def find_pdf_recursive(pdf_name, base_path="/input"):
    """
    Busca recursivamente un archivo PDF en el path base dado.
    Retorna la ruta completa si lo encuentra, o None si no.
    No imprime nada ni lanza excepciones.
    """
    try:
        if not base_path or not os.path.exists(base_path):
            return None

        for root, dirs, files in os.walk(base_path):
            if pdf_name in files:
                return os.path.join(root, pdf_name)
    except Exception:
        pass
    return None

def resolve_input_path(filename):
    """
    Resuelve la ruta completa del PDF basándose en la configuración (Docker vs Local)
    y realizando una búsqueda recursiva.
    """
    config = load_config()
    dockerized = config.get('dockerized', False)

    if dockerized:
        base_path = config.get('docker_input_path_prefix', '/input')
    else:
        base_path = config.get('local_input_path', '')

    if not base_path:
        # Fallback si no hay path configurado en local, usar current dir o "."
        base_path = "."

    return find_pdf_recursive(filename, base_path), base_path

def resolve_output_path():
    """
    Resuelve la ruta de salida basándose en la configuración.
    """
    config = load_config()
    dockerized = config.get('dockerized', False)

    if dockerized:
        return config.get('docker_output_path', '/output')
    else:
        return config.get('local_output_path', './Libros Atomicos')
