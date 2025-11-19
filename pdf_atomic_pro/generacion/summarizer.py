import re

def generate_fallback_summary(text_content: str) -> str:
    """
    Genera un resumen simple de respaldo tomando la primera oración del texto.
    """
    if not text_content:
        return ""

    # Busca la primera oración (termina en punto, interrogación o exclamación)
    match = re.search(r'([^.!?]+[.!?])', text_content)

    if match:
        summary = match.group(1).strip()
    else:
        # Si no se encuentra puntuación, toma la primera línea como respaldo
        summary = text_content.split('\n')[0].strip()

    return summary
