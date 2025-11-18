import re
from typing import List, Dict

def normalize_text(structured_lines: List[Dict], line_spacing_threshold_factor: float = 1.5) -> str:
    """
    Convierte una lista de líneas de texto estructuradas en una única cadena de texto,
    reconstruyendo párrafos y limpiando artefactos.
    """
    if not structured_lines:
        return ""

    text_parts = []
    previous_line_y1 = None
    previous_line_size = None

    for line_data in structured_lines:
        current_text = line_data.get('text', '').strip()
        if not current_text:
            continue

        current_y0 = line_data.get('y0')
        current_y1 = line_data.get('y1')
        current_size = line_data.get('size')

        if all(x is not None for x in [current_y0, current_y1, current_size, previous_line_y1, previous_line_size]):
            vertical_gap = current_y0 - previous_line_y1

            # Si el espacio vertical es grande, es un nuevo párrafo.
            if vertical_gap > (previous_line_size * line_spacing_threshold_factor):
                text_parts.append("\n\n")
            # Si no, es la misma línea o el mismo párrafo, así que unimos con un espacio.
            else:
                text_parts.append(" ")

        text_parts.append(current_text)
        previous_line_y1 = current_y1
        previous_line_size = current_size

    # 1. Unir todas las partes
    full_text = "".join(text_parts).strip()

    # 2. Limpieza y Normalización

    # Eliminar espacios múltiples que no sean saltos de línea
    cleaned_text = re.sub(r'[ \t]+', ' ', full_text)

    # Corregir espaciado alrededor de los saltos de párrafo
    cleaned_text = re.sub(r'\s*\n\n\s*', '\n\n', cleaned_text)

    # Eliminar líneas que solo contienen números (probables números de página)
    lines = cleaned_text.split('\n')
    cleaned_lines = [line for line in lines if not re.fullmatch(r'\s*\d+\s*', line)]
    cleaned_text = "\n".join(cleaned_lines)

    # Normalizar múltiples saltos de línea a un máximo de dos
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

    # Eliminar caracteres problemáticos de UTF-8
    cleaned_text = cleaned_text.encode('utf-8', 'ignore').decode('utf-8')

    return cleaned_text.strip()
