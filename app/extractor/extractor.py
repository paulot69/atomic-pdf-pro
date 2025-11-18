import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from collections import Counter
import re

def _clean_repeated_headers_footers_structured(pages_structured_text: list[list[dict]], top_n_lines=3, bottom_n_lines=3, min_occurrence_ratio=0.5) -> list[list[dict]]:
    """Identifies and removes common headers and footers from structured page text."""
    header_candidates = []
    footer_candidates = []

    for page_lines in pages_structured_text:
        if len(page_lines) > (top_n_lines + bottom_n_lines):
            header_candidates.extend([line['text'] for line in page_lines[:top_n_lines]])
            footer_candidates.extend([line['text'] for line in page_lines[-bottom_n_lines:]])

    header_counts = Counter(line.strip() for line in header_candidates if line.strip())
    footer_counts = Counter(line.strip() for line in footer_candidates if line.strip())

    num_pages = len(pages_structured_text)
    lines_to_remove = set()

    min_occurrences = int(num_pages * min_occurrence_ratio)
    if min_occurrences < 2:
        min_occurrences = 2

    for line, count in header_counts.items():
        if count >= min_occurrences:
            if re.fullmatch(r'\d+', line) or len(line) < 70:
                lines_to_remove.add(line)

    for line, count in footer_counts.items():
        if count >= min_occurrences:
            if re.fullmatch(r'\d+', line) or len(line) < 70:
                lines_to_remove.add(line)

    if lines_to_remove:
        print(f"Identified and removed {len(lines_to_remove)} common header/footer line(s).")

    cleaned_pages_structured_text = []
    for page_lines in pages_structured_text:
        cleaned_page_lines = [line for line in page_lines if line['text'].strip() not in lines_to_remove]
        cleaned_pages_structured_text.append(cleaned_page_lines)

    return cleaned_pages_structured_text

def _extract_text_with_pymupdf(pdf_path) -> list[list[dict]]:
    """
    Extracts text and basic font information (size, bold) from a PDF using PyMuPDF.
    Returns a list of lists, where each inner list represents a page,
    and contains dictionaries for each line with 'text', 'size', 'is_bold'.
    """
    all_pages_structured_text = []
    with fitz.open(pdf_path) as doc:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text_blocks = page.get_text("dict") # Get text in dictionary format
            
            page_lines = []
            for block in text_blocks['blocks']:
                if block['type'] == 0: # Text block
                    for line in block['lines']:
                        line_text = ""
                        line_font_sizes = []
                        line_is_bold = False
                        
                        for span in line['spans']:
                            line_text += span['text']
                            line_font_sizes.append(span['size'])
                            if 'bold' in span['font'].lower(): # Check for 'bold' in font name
                                line_is_bold = True
                        
                        if line_text.strip(): # Only add non-empty lines
                            # Use the average or max font size for the line
                            avg_font_size = sum(line_font_sizes) / len(line_font_sizes) if line_font_sizes else 0
                            page_lines.append({
                                "text": line_text.strip(),
                                "size": avg_font_size,
                                "is_bold": line_is_bold
                            })
            all_pages_structured_text.append(page_lines)
    return all_pages_structured_text

def _extract_text_with_ocr(pdf_path):
    """Extracts text from a PDF using OCR."""
    images = convert_from_path(pdf_path)
    return [pytesseract.image_to_string(image) for image in images]

def extract_text(pdf_path) -> list[list[dict]]:
    """
    Extracts text and font information from a PDF, determines if OCR is needed,
    and cleans common headers/footers.
    """
    structured_pages_text = []
    try:
        structured_pages_text = _extract_text_with_pymupdf(pdf_path)

        # Calculate total text length for fallback decision
        total_text_len = sum(len(line['text'].strip()) for page in structured_pages_text for line in page)

        # Fallback to OCR if text is minimal
        if total_text_len < 500:
            print("Minimal text extracted. Falling back to OCR...")
            ocr_pages_text = _extract_text_with_ocr(pdf_path)
            # Convert OCR plain text to structured format with default font info
            structured_pages_text = []
            for page_text in ocr_pages_text:
                page_lines = []
                for line in page_text.split('\n'):
                    if line.strip():
                        page_lines.append({"text": line.strip(), "size": 12.0, "is_bold": False}) # Default font info
                structured_pages_text.append(page_lines)
    except Exception as e:
        print(f"Warning: Could not process with PyMuPDF ({e}). Falling back to OCR.")
        ocr_pages_text = _extract_text_with_ocr(pdf_path)
        structured_pages_text = []
        for page_text in ocr_pages_text:
            page_lines = []
            for line in page_text.split('\n'):
                if line.strip():
                    page_lines.append({"text": line.strip(), "size": 12.0, "is_bold": False}) # Default font info
            structured_pages_text.append(page_lines)

    # Clean headers and footers from the extracted structured text
    cleaned_pages_structured_text = _clean_repeated_headers_footers_structured(structured_pages_text)

    return cleaned_pages_structured_text