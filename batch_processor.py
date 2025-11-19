import csv
import requests
import io
import os

# Importar la lógica de procesamiento principal
from main import process_pdf
from pdf_atomic_pro.estructura.indice_detector import TOCEntry

# URL del CSV publicado desde Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTiydVmQoG5Qg9Qij_H7gxjLOiFWTEKxijdK9rST1M_ZzhZAKstDAcg49alka3WM4iWNUEffJ9aCjGo/pub?gid=0&single=true&output=csv"
DEFAULT_OUTPUT_DIR = "D:\\github\\Libros Atomicos"

def run_batch_process():
    """
    Lee el inventario de libros desde Google Sheets y procesa los que están marcados para atomizar,
    utilizando la lógica de pdf-atomic-pro directamente.
    """
    print("Descargando el inventario de libros desde Google Sheets...")
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        
        # Normalizar los nombres de las columnas (headers)
        reader.fieldnames = [name.strip().lower().replace('.', '') for name in reader.fieldnames]

        books_to_process = [row for row in reader if row.get('atomizar libro', '').strip().upper() == 'SI']

        if not books_to_process:
            print("No se encontraron libros marcados con 'SI' en la columna 'atomizar libro'.")
            return

        print(f"Se encontraron {len(books_to_process)} libro(s) para procesar.")

        for book in books_to_process:
            # Extraer y limpiar datos del CSV
            pdf_path = book.get('url local', '').strip().replace('"', '') # Limpiar comillas
            title = book.get('título original del libro', '').strip()
            author = book.get('autor (nombre apellido)', '').strip()
            year = book.get('año de publicación', '').strip()
            indice_str = book.get('indice', '').strip()
            thematic_folder = book.get('carpeta temática final', '').strip()
            theme_nomenclature = book.get('tema (para nomenclatura)', '').strip()
            generate_summaries = book.get('generar resumen', '').strip().upper() == 'SI'

            if not all([pdf_path, title, author, year]):
                print(f"ADVERTENCIA: Se omitió un libro por falta de datos. Título: '{title}', Ruta: '{pdf_path}'")
                continue

            # Parsear el índice si existe, detectando jerarquía por sangría
            toc_from_csv = []
            if indice_str:
                lines = [line for line in indice_str.split('\n') if line.strip()]
                for line in lines:
                    indentation = len(line) - len(line.lstrip(' \t'))
                    level = (indentation // 4) + 1
                    title_text = line.strip()
                    toc_from_csv.append(TOCEntry(title=title_text, page_number=-1, level=level))

                print(f"Índice explícito encontrado para '{title}' con {len(toc_from_csv)} entradas y estructura jerárquica.")

            print(f"\n--- Iniciando procesamiento para: {title} ---")
            
            # Llamar a la función de procesamiento directamente
            try:
                # Comprobación de existencia de archivo aquí para dar un feedback claro
                if not os.path.exists(pdf_path):
                    print(f"ERROR: No se pudo encontrar el archivo PDF en la ruta especificada: {pdf_path}")
                    print(f"Por favor, verifica la ruta en tu Google Sheet y que el disco G: esté accesible.")
                    print(f"Omitiendo el libro: '{title}'")
                    continue

                process_pdf(
                    pdf_path=pdf_path,
                    title=title,
                    author=author,
                    year=year,
                    output_dir=DEFAULT_OUTPUT_DIR,
                    toc_from_csv=toc_from_csv,
                    thematic_folder=thematic_folder,
                    theme_nomenclature=theme_nomenclature,
                    generate_summaries=generate_summaries
                )
                print(f"--- Procesamiento de '{title}' completado. ---")

            except Exception as e:
                print(f"--- ERROR: Ocurrió un error inesperado al procesar '{title}': {e} ---")

    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo CSV: {e}")
    except Exception as e:
        print(f"Ocurrió un error al leer o procesar el CSV: {e}")


if __name__ == "__main__":
    # Cambiar al directorio del script para que main.py y sus importaciones funcionen correctamente
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_batch_process()
