import re
from dataclasses import dataclass
from typing import List, Dict
from unidecode import unidecode
import fitz
import logging

@dataclass
class TOCEntry:
    raw_title: str
    title: str
    page_number: int
    level: int = 1

def _normalize_title(text: str) -> str:
    """A consistent normalization for matching titles."""
    text = unidecode(text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_toc_from_bookmarks(pdf_path: str) -> List[TOCEntry]:
    """Extracts the table of contents from the PDF bookmarks. This is the most reliable method."""
    toc_entries = []
    try:
        doc = fitz.open(pdf_path)
        bookmarks = doc.get_toc()
        if bookmarks:
            logging.info(f"Found {len(bookmarks)} entries in PDF bookmarks.")
            for level, title, page_num in bookmarks:
                # The title from bookmarks is usually clean already
                toc_entries.append(TOCEntry(raw_title=title, title=title, page_number=page_num, level=level))
    except Exception as e:
        logging.warning(f"Could not extract bookmarks from PDF: {e}")
    return toc_entries

def detect_toc_entries(pages_structured_text: List[List[Dict]], toc_page_limit=10) -> List[TOCEntry]:
    """
    Robustly extracts Table of Contents entries by scanning the text of the first few pages.
    The core principle is that a valid TOC entry MUST contain both a title and a page number on the same line.
    """
    toc_structured_lines = [line for page in pages_structured_text[:toc_page_limit] for line in page]
    
    entries = []
    
    # This regex is the heart of the new, stricter detection. It looks for:
    # ^(?P<label>.+?)         - A non-greedy capture of the title text.
    # [\s\.\_]+               - A flexible separator of spaces, dots, or underscores.
    # (?P<page>\d+)$          - A number at the very end of the line, captured as the page.
    # The (?!\.) part is a negative lookahead to avoid matching mid-sentence periods.
    toc_line_pattern = re.compile(r"^(?P<label>\s*.+?)\s+(?P<page>\d+)$")

    # Regex to clean up common chapter/section prefixes from the title.
    prefix_cleaner_pattern = re.compile(r"^\s*(cap[ií]tulo|chapter|secci[oó]n|section|parte|part|cap\.?)\s*([IVXLCDM\d]+[:.\s-]*)?", re.IGNORECASE)

    # --- Stage 1: Search for an explicit "Contents" or "Índice" line ---
    toc_keyword_pattern = re.compile(r'^(ÍNDICE|INDEX|CONTENIDO|TABLA DE CONTENIDO|SUMARIO|CONTENTS|TABLE OF CONTENTS)$', re.IGNORECASE)
    toc_start_index = -1
    for i, line_data in enumerate(toc_structured_lines):
        if toc_keyword_pattern.match(line_data['text'].strip()):
            toc_start_index = i
            logging.info(f"Found explicit TOC keyword '{line_data['text'].strip()}' on line {i}.")
            break

    # If a keyword was found, start searching from there. Otherwise, search all lines.
    search_area = toc_structured_lines[toc_start_index + 1:] if toc_start_index != -1 else toc_structured_lines

    # --- Stage 2: Apply the robust line pattern to the search area ---
    for line_data in search_area:
        text = line_data['text'] # Removed .strip() to preserve leading spaces
        if not text.strip(): # Check for empty content after stripping for conditional logic
            continue

        match = toc_line_pattern.match(text)
        if match:
            raw_title = match.group('label') # Removed .strip() to preserve leading spaces
            page_str = match.group('page')
            
            # Basic validation: title should not be excessively long or short.
            if 2 < len(raw_title) < 200:
                # Clean the title for better matching later, but keep the raw title.
                cleaned_title = prefix_cleaner_pattern.sub('', raw_title).strip()
                
                # Further clean common artifacts left after prefix removal.
                cleaned_title = re.sub(r'^[.:\s]+', '', cleaned_title)
                cleaned_title = re.sub(r'[\.\s]+$', '', cleaned_title) # NEW: Remove trailing dots/whitespace

                if cleaned_title:
                    entries.append(TOCEntry(
                        raw_title=raw_title,
                        title=cleaned_title,
                        page_number=int(page_str),
                        level=1 # Level detection from text is unreliable; assume level 1.
                    ))

    logging.info(f"Heuristically detected {len(entries)} entries from the document's text-based Table of Contents.")
    if entries:
        # Simple heuristic to detect hierarchy: if a title starts with more spaces, it's a sublevel.
        # This is fragile but can add value if the TOC is well-formatted.
        min_spaces = float('inf')
        for entry in entries:
             leading_spaces = len(entry.raw_title) - len(entry.raw_title.lstrip(' '))
             if leading_spaces < min_spaces:
                 min_spaces = leading_spaces
        
        for entry in entries:
            leading_spaces = len(entry.raw_title) - len(entry.raw_title.lstrip(' '))
            calculated_level = ((leading_spaces - min_spaces) // 2) + 1
            entry.level = calculated_level


    return entries

