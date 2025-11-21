import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from main import process_pdf
from pdf_atomic_pro.estructura.indice_detector import TOCEntry

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
HISTORY_FILE = "processed_history.log"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'llaves/torre_credentials.json'
RANGE_NAME = 'Hoja 1' # Asumimos que es la primera hoja, o se puede especificar
DEFAULT_OUTPUT_DIR = "./Libros Atomicos"

# --- Mapeo de Columnas (Normalizadas a minúsculas y sin puntos) ---
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
    """Carga el historial de archivos procesados."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def _add_to_history(filepath):
    """Añade un archivo al historial."""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{filepath}\n")

def get_sheet_data():
    """Obtiene los datos de Google Sheet usando Service Account."""
    try:
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        if not spreadsheet_id:
             raise ValueError("La variable de entorno SPREADSHEET_ID no está definida.")

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
        for row in values[1:]:
            # Asegurar que la fila tenga la misma longitud que el header
            row_dict = {header[i]: row[i].strip() if i < len(row) else '' for i in range(len(header))}
            data.append(row_dict)

        return data

    except Exception as e:
        logging.error(f"Error al conectar con Google Sheets: {e}")
        sys.exit(1)

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

def main():
    """
    Script principal para procesar libros desde Google Sheets usando Service Account.
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="Procesa libros desde Google Sheets para Atomic PDF.")
    parser.add_argument("--sin-ia", action="store_true", help="Desactiva la generación de metadatos con IA.")
    args = parser.parse_args()

    logging.info("Iniciando escaneo de Google Sheets...")

    # Obtener datos
    all_books = get_sheet_data()

    # Filtrar libros a procesar
    to_process = [
        book for book in all_books
        if book.get(COL_TRIGGER, '').strip().upper() == TRIGGER_VALUE
    ]

    if not to_process:
        logging.info("No se encontraron libros marcados con 'SI' para procesar.")
        return

    logging.info(f"Se encontraron {len(to_process)} libros para procesar.")

    processed_history = _load_history()

    for book in to_process:
        pdf_path = book.get(COL_PATH, '').replace('"', '')
        title = book.get(COL_TITLE, '')

        if not pdf_path:
            logging.warning(f"Libro '{title}' sin ruta de archivo. Saltando.")
            continue

        if pdf_path in processed_history:
            logging.info(f"Libro '{title}' ya procesado anteriormente. Saltando.")
            continue

        if not os.path.exists(pdf_path):
             logging.error(f"El archivo no existe: {pdf_path}. Verifica la ruta.")
             continue

        logging.info(f"Procesando: {title}")

        # Preparar datos
        author = book.get(COL_AUTHOR, '')
        year = book.get(COL_YEAR, '')
        indice_str = book.get(COL_INDEX, '')
        thematic_folder = book.get(COL_THEMATIC, '')
        theme_nomenclature = book.get(COL_THEME_NOMENCLATURE, '')
        generate_summaries_csv = book.get(COL_SUMMARY, '').upper() == 'SI'

        # Determinar uso de IA (Argumento CLI tiene precedencia o lógica combinada)
        # Si --sin-ia está activo, no se usa IA. Si no, depende del CSV o default True
        use_ai = not args.sin_ia

        # Parsear Índice
        toc_from_csv = parse_toc_from_string(indice_str)
        if toc_from_csv:
            logging.info(f"  - Índice personalizado detectado ({len(toc_from_csv)} entradas).")

        try:
            # Llamada directa a main.process_pdf
            process_pdf(
                pdf_path=pdf_path,
                title=title,
                author=author,
                year=year,
                output_dir=DEFAULT_OUTPUT_DIR,
                toc_from_csv=toc_from_csv,
                thematic_folder=thematic_folder,
                theme_nomenclature=theme_nomenclature,
                use_ai=use_ai,
                generate_summaries=generate_summaries_csv
            )

            _add_to_history(pdf_path)
            logging.info(f"ÉXITO: '{title}' procesado correctamente.")

        except Exception as e:
            logging.error(f"FALLO al procesar '{title}': {e}", exc_info=True)

if __name__ == "__main__":
    # Asegurar que estamos en el directorio raíz
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
