import os
import sys
import argparse
import pandas as pd
import subprocess
from dotenv import load_dotenv

# --- Constantes ---
HISTORY_FILE = "processed_history.log"
TRIGGER_COLUMN = "ATOMIZAR LIBRO."
PATH_COLUMN = "URL LOCAL"
TITLE_COLUMN = "Título Original del Libro"
AUTHOR_COLUMN = "Autor (Nombre Apellido)"
YEAR_COLUMN = "Año de Publicación"
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

def main():
    """
    Script principal para procesar libros desde una hoja de Google Sheets.
    """
    # --- Configuración ---
    load_dotenv()
    sheet_url = os.getenv("SHEET_CSV_URL")

    parser = argparse.ArgumentParser(description="Procesa libros desde Google Sheets para Atomic PDF.")
    parser.add_argument("--sin-ia", action="store_true", help="Desactiva la generación de metadatos con IA para todos los libros.")
    args = parser.parse_args()

    if not sheet_url:
        print("[ERROR] La variable SHEET_CSV_URL no está definida en el archivo .env.")
        sys.exit(1)

    # --- Carga de datos ---
    try:
        df = pd.read_csv(sheet_url)
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
    except Exception as e:
        print(f"[ERROR] No se pudo cargar o procesar el CSV desde la URL: {e}")
        sys.exit(1)

    # --- Filtrado ---
    # Asegurarse de que la columna exista
    if TRIGGER_COLUMN not in df.columns:
        print(f"[ERROR] No se encontró la columna disparadora '{TRIGGER_COLUMN}' en la hoja.")
        sys.exit(1)

    # Filtrar filas que deben ser procesadas
    to_process = df[df[TRIGGER_COLUMN].str.lower() == TRIGGER_VALUE.lower()]

    if to_process.empty:
        print("[INFO] No se encontraron nuevos libros para procesar marcados con 'SI'.")
        return

    # --- Procesamiento ---
    processed_history = _load_history()

    for index, row in to_process.iterrows():
        filepath = row.get(PATH_COLUMN)
        title = row.get(TITLE_COLUMN)

        if pd.isna(filepath) or not filepath:
            print(f"[WARN] Fila {index+2}: La ruta del archivo está vacía. Saltando.")
            continue

        filepath = filepath.strip()

        print("-" * 50)

        if filepath in processed_history:
            print(f"[SKIP] El libro '{title or filepath}' ya estaba en el historial.")
            continue

        if not os.path.exists(filepath):
            print(f"[WARN] El archivo para '{title}' no existe en la ruta especificada: {filepath}. Saltando.")
            continue

        print(f"[NUEVO] Detectado: {title or 'Sin Título'}")
        print(f"[PROCESANDO] Ejecutando Atomic PDF para: {filepath}")

        # --- Construcción del comando ---
        command = [
            sys.executable,  # Usar el mismo intérprete de Python
            "main.py",
            filepath
        ]

        # Añadir argumentos opcionales si existen
        if pd.notna(title) and title:
            command.extend(["--titulo", str(title)])
        if pd.notna(row.get(AUTHOR_COLUMN)) and row.get(AUTHOR_COLUMN):
            command.extend(["--autor", str(row.get(AUTHOR_COLUMN))])
        if pd.notna(row.get(YEAR_COLUMN)) and row.get(YEAR_COLUMN):
            # Asegurarse de que el año sea un entero antes de convertir a string
            try:
                year = int(row.get(YEAR_COLUMN))
                command.extend(["--ano", str(year)])
            except (ValueError, TypeError):
                 print(f"[WARN] El año '{row.get(YEAR_COLUMN)}' no es un número válido. Se omitirá.")

        if args.sin_ia:
            command.append("--sin-ia")

        # --- Ejecución del subproceso ---
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(result.stdout)
            print(f"[LISTO] El libro '{title}' fue procesado correctamente.")
            _add_to_history(filepath)

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Falló el procesamiento para el libro '{title}'.")
            print("--- Salida del Error ---")
            print(e.stdout)
            print(e.stderr)
            print("------------------------")
            # No se añade al historial para reintentar en la próxima ejecución

        except FileNotFoundError:
            print(f"[ERROR] No se pudo encontrar 'main.py'. Asegúrate de ejecutar 'sheet_runner.py' desde el directorio raíz del proyecto.")
            sys.exit(1)

if __name__ == "__main__":
    main()
