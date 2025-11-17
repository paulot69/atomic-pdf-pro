import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from collections import Counter
import re

def _clean_repeated_headers_footers(pages_text: list[str], top_n_lines=3, bottom_n_lines=3, min_occurrence_ratio=0.5) -> list[str]:
    """Identifies and removes common headers and footers from page text."""
    header_candidates = []
    footer_candidates = []

    for text in pages_text:
        lines = text.strip().split('\n')
        if len(lines) > (top_n_lines + bottom_n_lines):
            header_candidates.extend(lines[:top_n_lines])
            footer_candidates.extend(lines[-bottom_n_lines:])

    header_counts = Counter(line.strip() for line in header_candidates if line.strip())
    footer_counts = Counter(line.strip() for line in footer_candidates if line.strip())

    num_pages = len(pages_text)
    lines_to_remove = set()

    min_occurrences = int(num_pages * min_occurrence_ratio)
    if min_occurrences < 2:  # Ensure it doesn't trigger for very short documents
        min_occurrences = 2

    for line, count in header_counts.items():
        if count >= min_occurrences:
            # Check if it looks like a page number or a short, repetitive title
            if re.fullmatch(r'\d+', line) or len(line) < 70:
                lines_to_remove.add(line)

    for line, count in footer_counts.items():
        if count >= min_occurrences:
            if re.fullmatch(r'\d+', line) or len(line) < 70:
                lines_to_remove.add(line)

    if lines_to_remove:
        print(f"Identified and removed {len(lines_to_remove)} common header/footer line(s).")

    cleaned_pages = []
    for text in pages_text:
        lines = text.strip().split('\n')
        cleaned_lines = [line for line in lines if line.strip() not in lines_to_remove]
        cleaned_pages.append("\n".join(cleaned_lines))

    return cleaned_pages

def _extract_text_with_pymupdf(pdf_path):
    """Extracts text from a PDF using PyMuPDF."""
    with fitz.open(pdf_path) as doc:
        return [page.get_text() for page in doc]

def _extract_text_with_ocr(pdf_path):
    """Extracts text from a PDF using OCR."""
    images = convert_from_path(pdf_path)
    return [pytesseract.image_to_string(image) for image in images]

def extract_text(pdf_path) -> list[str]:
    """
    Extracts text from a PDF, determines if OCR is needed, and cleans common headers/footers.
    """
    try:
        pages_text = _extract_text_with_pymupdf(pdf_path)

        # Fallback to OCR if text is minimal
        if sum(len(page.strip()) for page in pages_text) < 500:
            print("Minimal text extracted. Falling back to OCR...")
            pages_text = _extract_text_with_ocr(pdf_path)
    except Exception as e:
        print(f"Warning: Could not process with PyMuPDF ({e}). Falling back to OCR.")
        pages_text = _extract_text_with_ocr(pdf_path)

    # Clean headers and footers from the extracted text
    cleaned_pages_text = _clean_repeated_headers_footers(pages_text)

    return cleaned_pages_text
