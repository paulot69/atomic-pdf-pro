from googletrans import Translator, LANGUAGES
import time
import logging
from typing import List, Dict

def translate_text(text: str, dest_lang: str) -> str:
    """Traduce un texto al idioma de destino con reintentos."""
    if not dest_lang in LANGUAGES:
        logging.error(f"Idioma de destino no válido: {dest_lang}")
        return text

    translator = Translator()
    retries = 3
    delay = 1  # segundos

    for attempt in range(retries):
        try:
            # La librería puede manejar listas de strings, pero para ser más robustos,
            # lo haremos uno por uno o en pequeños lotes si fuera necesario.
            # Por ahora, un solo texto a la vez.
            translated = translator.translate(text, dest=dest_lang)
            return translated.text
        except Exception as e:
            logging.warning(f"Error en la traducción (intento {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error("No se pudo traducir el texto después de varios intentos.")
                return text # Devuelve el texto original si falla

def translate_chapters(chapters: List[Dict], dest_lang: str) -> List[Dict]:
    """
    Recorre la estructura de capítulos y traduce los títulos y el contenido
    de cada sección.
    """
    logging.info(f"Iniciando traducción al '{dest_lang}'...")

    for chapter in chapters:
        # Traducir el título del capítulo
        if chapter.get('title'):
            chapter['title'] = translate_text(chapter['title'], dest_lang)

        # Traducir los títulos y el contenido de las secciones
        if chapter.get('sections'):
            for section in chapter['sections']:
                if section.get('title'):
                    section['title'] = translate_text(section['title'], dest_lang)
                if section.get('content'):
                    section['content'] = translate_text(section['content'], dest_lang)

    logging.info("Traducción completada.")
    return chapters
