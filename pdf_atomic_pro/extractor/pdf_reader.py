import fitz  # PyMuPDF
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

def extract_text_with_pymupdf(pdf_path) -> list[list[dict]]:
    """
    Extracts text and detailed font information (font, size, bold) from a PDF using PyMuPDF.
    Returns a list of lists, where each inner list represents a page,
    and contains dictionaries for each line with 'text', 'font', 'size', 'is_bold'.
    """
    all_pages_structured_text = []
    with fitz.open(pdf_path) as doc:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            # Use the "dict" format, which is an alias for "json" with more structure.
            text_blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES)
            
            page_lines = []
            if 'blocks' in text_blocks:
                for block in text_blocks['blocks']:
                    if block.get('type') == 0: # Text block
                        for line in block.get('lines', []):
                            if not line.get('spans'): continue

                            # Combine text from all spans in the line
                            line_text = "".join(span.get('text', '') for span in line['spans']).strip()
                            if not line_text: continue

                            # --- Font Style Logic ---
                            # Use the style of the first span as representative for the line.
                            first_span = line['spans'][0]
                            line_font = first_span.get('font', 'Unknown')
                            line_size = first_span.get('size', 0)
                            # The 'flags' integer is a bitmask. Bold is the 5th bit (2**4).
                            line_is_bold = (first_span.get('flags', 0) & 2**4) > 0

                            page_lines.append({
                                "text": line_text,
                                "font": line_font,
                                "size": line_size,
                                "is_bold": line_is_bold,
                                "y0": line['bbox'][1],
                                "y1": line['bbox'][3]
                            })
            all_pages_structured_text.append(page_lines)
    return _clean_repeated_headers_footers_structured(all_pages_structured_text)
