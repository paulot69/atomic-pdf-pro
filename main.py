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
import sys
from pdf_atomic_pro.traduccion import traductor

# Setup logging
log_file_path = os.path.join(os.path.dirname(__file__), 'main_debug.log')
# Clear previous log file
if os.path.exists(log_file_path):
    os.remove(log_file_path)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)

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

def process_pdf(pdf_path, title, author, year, output_dir, translate_to=None, toc_from_csv=None, thematic_folder=None, theme_nomenclature=None, use_ai=True, generate_summaries=True):
    """
    Processes a single PDF file into an atomic Obsidian vault.

    Args:
        pdf_path (str): The full path to the PDF file.
        title (str): The title of the book.
        author (str): The author of the book.
        year (str): The publication year.
        output_dir (str): The root directory for the generated vault.
        translate_to (str, optional): The language to translate the content to. Defaults to None.
        toc_from_csv (List[TOCEntry], optional): An explicit list of chapter entries from CSV. Defaults to None.
        thematic_folder (str, optional): The thematic folder for domain tags.
        theme_nomenclature (str, optional): The theme nomenclature for sub-domain tags.
        use_ai (bool): Whether to use the AI for metadata generation.
        generate_summaries (bool): Whether to generate summaries for each atomic note.
    """
    # --- Temporary Directory Setup ---
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Using temporary directory: {temp_dir}")

    try:
        # --- Processing Pipeline ---
        logging.info(f"Starting processing for '{title}' by {author} ({year})")

        # 1. Text Extraction
        logging.info("Extracting text from PDF...")
        try:
            # First, try the standard text extraction
            structured_text = pdf_reader.extract_text_with_pymupdf(pdf_path)
            # Heuristic to check if extraction was successful
            if not any(page_lines for page_lines in structured_text):
                 raise ValueError("PyMuPDF extracted no text content.")
        except Exception as e:
            logging.warning(f"Standard text extraction with PyMuPDF failed or returned empty: {e}. Attempting OCR fallback...")
            # Fallback to OCR if the initial method fails
            structured_text = ocr_handler.extract_text_with_ocr(pdf_path)
        
        if not any(page_lines for page_lines in structured_text):
            raise ValueError("No text could be extracted from the PDF, even with OCR.")

        # 2. TOC Detection and Structuring
        logging.info("Structuring chapters...")
        toc_entries = []
        is_inferred = False

        if toc_from_csv:
            logging.info("Using explicit TOC from CSV to find chapter locations.")
            toc_entries = toc_from_csv
            # The _find_headers_with_toc function now directly returns all necessary info,
            # including the level. No reconstruction is needed here.
            header_locations = jerarquia._find_headers_with_toc(
                [line for page in structured_text for line in page],
                toc_entries
            )
            # If matches are found, we proceed. Otherwise, the fallback logic will trigger.
            if not header_locations:
                 logging.warning("Could not match any CSV TOC entries in the document text. Will attempt fallback.")
                 toc_entries = [] # Clear toc_entries to ensure fallback is used

        if not toc_entries:
            logging.info("No CSV TOC or matches found, detecting TOC from PDF bookmarks...")
            toc_entries = indice_detector.detect_toc_from_bookmarks(pdf_path)
            if not toc_entries:
                logging.info("No bookmarks found, searching for TOC in text...")
                # Flatten structured_text for TOC detection
                plain_text_for_toc = "\n".join([line['text'] for page in structured_text for line in page])
                toc_entries = indice_detector.detect_toc_entries(plain_text_for_toc)

        if not toc_entries:
            logging.warning("No reliable TOC found. Structure will be inferred sequentially (fallback).")
            is_inferred = True
        
        # The split_into_chapters function will use the found/provided toc_entries
        # and then apply the sub-section splitting logic internally.
        chapters = jerarquia.split_into_chapters(structured_text, toc_entries)

        # --- Optional Translation ---
        if translate_to:
            chapters = traductor.translate_chapters(chapters, translate_to)

        # 3. Vault Creation in Temp Directory
        sanitized_title = notas_atomicas._sanitize_title_for_filename(title)
        sanitized_author = notas_atomicas._sanitize_title_for_filename(author)

        book_root_name = f"{year} - {sanitized_title} - {sanitized_author}"
        if is_inferred:
            book_root_name = f"[FI] - {book_root_name}"

        temp_book_root_path = os.path.join(temp_dir, book_root_name)
        os.makedirs(temp_book_root_path, exist_ok=True)

        logging.info(f"Generating vault in temporary directory...")

        # 4. Note and MOC Generation
        atomic_chapters = notas_atomicas.process_and_write_atomic_notes(
            chapters, title, author, year, temp_book_root_path,
            thematic_folder=thematic_folder,
            theme_nomenclature=theme_nomenclature,
            use_ai=use_ai,
            generate_summaries=generate_summaries
        )
        mocs.write_mocs(temp_book_root_path, title, author, year, atomic_chapters)

        # 5. Link Verification
        logging.info("Verifying link integrity...")
        broken_links = verificador_links.verify_links(Path(temp_book_root_path))
        if broken_links:
            logging.warning("Broken links found:")
            for link in broken_links:
                logging.warning(f"  - In '{link['source_file']}': [[{link['broken_link']}]]")

        # --- Finalization: Move to final location ---
        final_output_path = os.path.join(output_dir, book_root_name)
        if os.path.exists(final_output_path):
            logging.warning(f"Destination directory already exists: {final_output_path}. It will be overwritten.")
            shutil.rmtree(final_output_path)
        
        # shutil.move works across different drives (like from temp C: to G:)
        shutil.move(temp_book_root_path, final_output_path)
        logging.info(f"Processing successfully completed. Vault saved at: {final_output_path}")
        return True

    except Exception as e:
        logging.error(f"A fatal error occurred during processing: {e}", exc_info=True)
        return False

    finally:
        # --- Temporary Directory Cleanup ---
        logging.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to an Atomic Obsidian Vault.")
    parser.add_argument("pdf_path", help="Path to the PDF file to process.")
    parser.add_argument("--titulo", help="Title of the book.")
    parser.add_argument("--autor", help="Author of the book.")
    parser.add_argument("--ano", help="Publication year of the book.")
    parser.add_argument("--salida", default="D:\\02_DEV_LAB\\00_GITHUB_REPOS\\Libros_Atomicos", help="Output directory for the atomic vault.")
    parser.add_argument("--traducir-a", help="Translate content to the specified language (e.g., 'es').")
    parser.add_argument("--sin-ia", action="store_true", help="Desactiva la generación de metadatos con IA y usa el fallback local.")

    args = parser.parse_args()

    # --- Metadata Handling ---
    pdf_title, pdf_author, pdf_year = get_pdf_metadata(args.pdf_path)

    title = args.titulo if args.titulo else pdf_title
    author = args.autor if args.autor else pdf_author
    year = args.ano if args.ano else pdf_year

    if not title:
        title = input("Please enter the title of the book: ")
    if not author:
        author = input("Please enter the author of the book: ")
    if not year:
        year = input("Please enter the publication year of the book: ")
    
    # Call the main processing function
    success = process_pdf(
        pdf_path=args.pdf_path, 
        title=title, 
        author=author, 
        year=year, 
        output_dir=args.salida, 
        translate_to=args.traducir_a,
        use_ai=not args.sin_ia
    )

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

