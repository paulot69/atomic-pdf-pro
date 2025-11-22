import os
import fitz  # PyMuPDF
import re
import logging
from pathlib import Path
import tempfile
import shutil
import sys

from pdf_atomic_pro.core.extractor import pdf_reader, ocr_handler
from pdf_atomic_pro.core.estructura import indice_detector, jerarquia
from pdf_atomic_pro.core.generacion import notas_atomicas, mocs
from pdf_atomic_pro.core.integridad import verificador_links
from pdf_atomic_pro.core.traduccion import traductor

# Setup logging (Note: This might be better configured centrally or via the API)
# keeping it simple for now or relying on the caller to configure logging.
logger = logging.getLogger(__name__)


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
        logger.warning(f"Could not extract metadata from PDF: {e}")
        return '', '', ''

def process_pdf(
    pdf_path,
    title,
    author,
    year,
    output_dir,
    translate_to=None,
    toc_from_csv=None,
    thematic_folder=None,
    theme_nomenclature=None,
    use_ai=True,
    generate_summaries=True,
    progress_callback=None
):
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
        progress_callback (callable, optional): A function to report progress (0-100).
    """
    if progress_callback: progress_callback(5, "Iniciando...")

    # --- Temporary Directory Setup ---
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Using temporary directory: {temp_dir}")

    try:
        # --- Processing Pipeline ---
        logger.info(f"Starting processing for '{title}' by {author} ({year})")
        if progress_callback: progress_callback(10, "Extrayendo texto...")

        # 1. Text Extraction
        logger.info("Extracting text from PDF...")
        try:
            # First, try the standard text extraction
            structured_text = pdf_reader.extract_text_with_pymupdf(pdf_path)
            # Heuristic to check if extraction was successful
            if not any(page_lines for page_lines in structured_text):
                 raise ValueError("PyMuPDF extracted no text content.")
        except Exception as e:
            logger.warning(f"Standard text extraction with PyMuPDF failed or returned empty: {e}. Attempting OCR fallback...")
            if progress_callback: progress_callback(15, "Aplicando OCR (puede tardar)...")
            # Fallback to OCR if the initial method fails
            structured_text = ocr_handler.extract_text_with_ocr(pdf_path)
        
        if not any(page_lines for page_lines in structured_text):
            raise ValueError("No text could be extracted from the PDF, even with OCR.")

        # 2. TOC Detection and Structuring
        if progress_callback: progress_callback(30, "Analizando estructura...")
        logger.info("Structuring chapters...")
        toc_entries = []
        is_inferred = False

        if toc_from_csv:
            logger.info("Using explicit TOC from CSV to find chapter locations.")
            toc_entries = toc_from_csv
            # The _find_headers_with_toc function now directly returns all necessary info,
            # including the level. No reconstruction is needed here.
            header_locations = jerarquia._find_headers_with_toc(
                [line for page in structured_text for line in page],
                toc_entries
            )
            # If matches are found, we proceed. Otherwise, the fallback logic will trigger.
            if not header_locations:
                 logger.warning("Could not match any CSV TOC entries in the document text. Will attempt fallback.")
                 toc_entries = [] # Clear toc_entries to ensure fallback is used

        if not toc_entries:
            logger.info("No CSV TOC or matches found, detecting TOC from PDF bookmarks...")
            toc_entries = indice_detector.detect_toc_from_bookmarks(pdf_path)
            if not toc_entries:
                logger.info("No bookmarks found, searching for TOC in text...")
                # Flatten structured_text for TOC detection
                plain_text_for_toc = "\n".join([line['text'] for page in structured_text for line in page])
                toc_entries = indice_detector.detect_toc_entries(plain_text_for_toc)

        if not toc_entries:
            logger.warning("No reliable TOC found. Structure will be inferred sequentially (fallback).")
            is_inferred = True
        
        # The split_into_chapters function will use the found/provided toc_entries
        # and then apply the sub-section splitting logic internally.
        chapters = jerarquia.split_into_chapters(structured_text, toc_entries)

        # --- Optional Translation ---
        if translate_to:
            if progress_callback: progress_callback(40, f"Traduciendo a {translate_to}...")
            chapters = traductor.translate_chapters(chapters, translate_to)

        # 3. Vault Creation in Temp Directory
        if progress_callback: progress_callback(50, "Generando Notas Atómicas...")
        sanitized_title = notas_atomicas._sanitize_title_for_filename(title)
        sanitized_author = notas_atomicas._sanitize_title_for_filename(author)

        book_root_name = f"{year} - {sanitized_title} - {sanitized_author}"
        if is_inferred:
            book_root_name = f"[FI] - {book_root_name}"

        temp_book_root_path = os.path.join(temp_dir, book_root_name)
        os.makedirs(temp_book_root_path, exist_ok=True)

        logger.info(f"Generating vault in temporary directory...")

        # 4. Note and MOC Generation
        # This part can be slow, might want to instrument process_and_write_atomic_notes for finer progress if possible
        # For now, we'll jump progress after it's done.
        atomic_chapters = notas_atomicas.process_and_write_atomic_notes(
            chapters, title, author, year, temp_book_root_path,
            thematic_folder=thematic_folder,
            theme_nomenclature=theme_nomenclature,
            use_ai=use_ai,
            generate_summaries=generate_summaries
        )

        if progress_callback: progress_callback(80, "Creando Mapas de Contenido (MOCs)...")
        mocs.write_mocs(temp_book_root_path, title, author, year, atomic_chapters)

        # 5. Link Verification
        if progress_callback: progress_callback(90, "Verificando enlaces...")
        logger.info("Verifying link integrity...")
        broken_links = verificador_links.verify_links(Path(temp_book_root_path))
        if broken_links:
            logger.warning("Broken links found:")
            for link in broken_links:
                logger.warning(f"  - In '{link['source_file']}': [[{link['broken_link']}]]")

        # --- Finalization: Move to final location ---
        if progress_callback: progress_callback(95, "Finalizando y moviendo archivos...")
        final_output_path = os.path.join(output_dir, book_root_name)
        if os.path.exists(final_output_path):
            logger.warning(f"Destination directory already exists: {final_output_path}. It will be overwritten.")
            shutil.rmtree(final_output_path)
        
        # shutil.move works across different drives (like from temp C: to G:)
        shutil.move(temp_book_root_path, final_output_path)
        logger.info(f"Processing successfully completed. Vault saved at: {final_output_path}")

        if progress_callback: progress_callback(100, "Completado.")
        return True

    except Exception as e:
        logger.error(f"A fatal error occurred during processing: {e}", exc_info=True)
        if progress_callback: progress_callback(-1, f"Error: {str(e)}")
        return False

    finally:
        # --- Temporary Directory Cleanup ---
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
             logger.warning(f"Could not remove temp directory: {e}")
