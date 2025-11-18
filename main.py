import argparse
import os
import fitz  # PyMuPDF
import re
import logging
from pathlib import Path
import tempfile
import shutil
from pdf_atomic_pro.extractor import pdf_reader, ocr_handler
from pdf_atomic_pro.estructura import indice_detector, jerarquia
from pdf_atomic_pro.generacion import notas_atomicas, mocs
from pdf_atomic_pro.integridad import verificador_links
from pdf_atomic_pro.traduccion import traductor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_pdf_metadata(pdf_path):
    """Extracts metadata (title, author, year) from the PDF."""
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        title = metadata.get('title', '')
        author = metadata.get('author', '')
        # Year might be in the creation date
        date = metadata.get('creationDate', '')
        year_match = re.search(r'(\d{4})', date) if date else None
        year = year_match.group(1) if year_match else ''
        return title, author, year
    except Exception as e:
        logging.warning(f"Could not extract metadata from PDF: {e}")
        return '', '', ''

def main():
    parser = argparse.ArgumentParser(description="Convierte un PDF a un Vault de Obsidian Atómico.")
    parser.add_argument("pdf_path", help="Ruta al archivo PDF a procesar.")
    parser.add_argument("--titulo", help="Título del libro.")
    parser.add_argument("--autor", help="Autor del libro.")
    parser.add_argument("--ano", help="Año de publicación del libro.")
    parser.add_argument("--salida", default="D:\\github\\Libros Atomicos", help="Directorio de salida para el vault atómico.")
    parser.add_argument("--traducir-a", help="Activa la traducción al idioma especificado (ej. 'es').")

    args = parser.parse_args()

    # --- Metadata Handling ---
    pdf_title, pdf_author, pdf_year = get_pdf_metadata(args.pdf_path)

    title = args.titulo if args.titulo else pdf_title
    author = args.autor if args.autor else pdf_author
    year = args.ano if args.ano else pdf_year

    if not title:
        title = input("Por favor, introduce el título del libro: ")
    if not author:
        author = input("Por favor, introduce el autor del libro: ")
    if not year:
        year = input("Por favor, introduce el año de publicación del libro: ")

    # --- Temporary Directory Setup ---
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Usando directorio temporal: {temp_dir}")

    try:
        # --- Processing Pipeline ---
        logging.info(f"Iniciando procesamiento para '{title}' por {author} ({year})")

        # 1. Extracción de Texto
        logging.info("Extrayendo texto del PDF...")
        try:
            structured_text = pdf_reader.extract_text_with_pymupdf(args.pdf_path)
            if not any(structured_text):
                raise ValueError("No text extracted")
        except Exception as e:
            logging.warning(f"PyMuPDF falló ({e}), intentando con OCR...")
            structured_text = ocr_handler.extract_text_with_ocr(args.pdf_path)

        # 2. Detección de Índice y Estructuración
        logging.info("Detectando índice y estructurando capítulos...")
        toc_entries = indice_detector.detect_toc_from_bookmarks(args.pdf_path)
        is_inferred = False
        if not toc_entries:
            logging.info("No se encontraron bookmarks, buscando índice en el texto...")
            toc_entries = indice_detector.detect_toc_entries(structured_text)

        if not toc_entries:
            logging.warning("No se encontró un índice fiable. La estructura será inferida secuencialmente.")
            is_inferred = True

        chapters = jerarquia.split_into_chapters(structured_text, toc_entries)

        # --- Optional Translation ---
        if args.traducir_a:
            chapters = traductor.translate_chapters(chapters, args.traducir_a)

        # 3. Creación del Vault en Directorio Temporal
        sanitized_title = notas_atomicas._sanitize_title_for_filename(title)
        sanitized_author = notas_atomicas._sanitize_title_for_filename(author)

        book_root_name = f"{year} - {sanitized_title} - {sanitized_author}"
        if is_inferred:
            book_root_name = f"[FI] - {book_root_name}"

        temp_book_root_path = os.path.join(temp_dir, book_root_name)
        os.makedirs(temp_book_root_path, exist_ok=True)

        logging.info(f"Generando vault en directorio temporal...")

        # 4. Generación de Notas y MOCs
        atomic_chapters = notas_atomicas.process_and_write_atomic_notes(chapters, title, author, year, temp_book_root_path)
        mocs.write_mocs(temp_book_root_path, title, atomic_chapters)

        # 5. Verificación de Enlaces
        logging.info("Verificando la integridad de los enlaces...")
        broken_links = verificador_links.verify_links(Path(temp_book_root_path))
        if broken_links:
            logging.warning("Se encontraron enlaces rotos:")
            for link in broken_links:
                logging.warning(f"  - En '{link['source_file']}': [[{link['broken_link']}]]")

        # --- Finalización: Mover a la ubicación final ---
        final_output_path = os.path.join(args.salida, book_root_name)
        if os.path.exists(final_output_path):
            logging.warning(f"El directorio de destino ya existe: {final_output_path}. Se sobrescribirá.")
            shutil.rmtree(final_output_path)

        shutil.move(temp_book_root_path, args.salida)
        logging.info(f"Procesamiento completado con éxito. Vault guardado en: {final_output_path}")

    except Exception as e:
        logging.error(f"Ha ocurrido un error fatal durante el procesamiento: {e}", exc_info=True)
        # No es necesario limpiar el directorio temporal aquí, ya que el bloque `finally` se encargará.

    finally:
        # --- Limpieza del Directorio Temporal ---
        logging.info(f"Limpiando directorio temporal: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
