import os
import sys
import logging
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from pdf_atomic_pro.core.pipeline import process_pdf
from pdf_atomic_pro.core.estructura.indice_detector import TOCEntry

# --- Configuración de Logging ---
logger = logging.getLogger(__name__)

# --- Constantes ---
HISTORY_FILE = "history.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'llaves/torre_credentials.json'
RANGE_NAME = 'Hoja 1'
DEFAULT_OUTPUT_DIR = "./Libros Atomicos"

# --- Mapeo de Columnas ---
COL_TRIGGER = "atomizar libro"
COL_PATH = "url local"
COL_TITLE = "título original del libro"
COL_AUTHOR = "autor (nombre apellido)"
COL_YEAR = "año de publicación"
COL_INDEX = "indice"
COL_THEMATIC = "carpeta temática final"
COL_THEME_NOMENCLATURE = "tema (para nomenclatura)"
COL_SUMMARY = "generar resumen"
TRIGGER_VALUE = "SI"

def _load_history():
    """Carga el historial de archivos procesados desde JSON."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def _add_to_history(entry):
    """Añade una entrada al historial."""
    history = _load_history()
    # Check for duplicates based on filepath
    if not any(h.get('filepath') == entry['filepath'] for h in history):
        history.append(entry)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

def is_processed(filepath):
    history = _load_history()
    return any(h.get('filepath') == filepath for h in history)

def get_sheet_data(spreadsheet_id=None):
    """Obtiene los datos de Google Sheet usando Service Account."""
    try:
        # If ID not passed, try env var
        if not spreadsheet_id:
            load_dotenv()
            spreadsheet_id = os.getenv("SPREADSHEET_ID")

        if not spreadsheet_id:
             raise ValueError("SPREADSHEET_ID no definido.")

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
             raise FileNotFoundError(f"No se encontró el archivo de credenciales: {SERVICE_ACCOUNT_FILE}")

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            return []

        # Convertir lista de listas a lista de diccionarios
        header = [h.strip().lower().replace('.', '') for h in values[0]]
        data = []
        for i, row in enumerate(values[1:], start=1): # start=1 means row index matches sheet (approx)
            # Asegurar que la fila tenga la misma longitud que el header
            row_dict = {header[j]: row[j].strip() if j < len(row) else '' for j in range(len(header))}
            row_dict['row_index'] = i + 1 # 1-based index for UI
            data.append(row_dict)

        return data

    except Exception as e:
        logger.error(f"Error al conectar con Google Sheets: {e}")
        raise e

def parse_toc_from_string(indice_str):
    """Parsea la cadena de índice en objetos TOCEntry."""
    if not indice_str:
        return []

    toc_entries = []
    lines = [line for line in indice_str.split('\n') if line.strip()]
    for line in lines:
        # Detectar nivel por indentación (4 espacios = 1 nivel)
        indentation = len(line) - len(line.lstrip(' \t'))
        level = (indentation // 4) + 1
        title_text = line.strip()
        toc_entries.append(TOCEntry(title=title_text, page_number=-1, level=level))
    return toc_entries

def process_batch(no_ai=False, translate_to=None, update_progress_func=None):
    """
    Procesa todos los libros marcados en el Sheet.
    """
    try:
        all_books = get_sheet_data()
        to_process = [
            book for book in all_books
            if book.get(COL_TRIGGER, '').strip().upper() == TRIGGER_VALUE
        ]

        if not to_process:
            logger.info("No se encontraron libros para procesar.")
            return 0

        count = 0
        total = len(to_process)

        for i, book in enumerate(to_process):
            if update_progress_func:
                update_progress_func(i, total, f"Procesando {i+1}/{total}: {book.get(COL_TITLE)}")

            pdf_path = book.get(COL_PATH, '').replace('"', '')
            title = book.get(COL_TITLE, '')

            if not pdf_path or not os.path.exists(pdf_path):
                logger.error(f"Archivo no encontrado: {pdf_path}")
                continue

            if is_processed(pdf_path):
                 logger.info(f"Saltando {title}, ya procesado.")
                 continue

            # Run Pipeline
            toc_from_csv = parse_toc_from_string(book.get(COL_INDEX, ''))
            use_ai = not no_ai

            success = process_pdf(
                pdf_path=pdf_path,
                title=title,
                author=book.get(COL_AUTHOR, ''),
                year=book.get(COL_YEAR, ''),
                output_dir=DEFAULT_OUTPUT_DIR,
                toc_from_csv=toc_from_csv,
                thematic_folder=book.get(COL_THEMATIC, ''),
                theme_nomenclature=book.get(COL_THEME_NOMENCLATURE, ''),
                use_ai=use_ai,
                generate_summaries=book.get(COL_SUMMARY, '').upper() == 'SI',
                translate_to=translate_to,
                progress_callback=None # We track batch progress, not internal per-book progress here
            )

            if success:
                _add_to_history({
                    "title": title,
                    "filepath": pdf_path,
                    "date": "TODO: Timestamp"
                })
                count += 1

        return count

    except Exception as e:
        logger.error(f"Error en batch process: {e}")
        raise e
