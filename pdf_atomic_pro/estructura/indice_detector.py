import re
from dataclasses import dataclass
from typing import List, Dict
from unidecode import unidecode
import fitz
import logging

@dataclass
class TOCEntry:
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
    """Extracts the table of contents from the PDF bookmarks."""
    toc_entries = []
    try:
        doc = fitz.open(pdf_path)
        bookmarks = doc.get_toc()
        if bookmarks:
            logging.info(f"Found {len(bookmarks)} entries in PDF bookmarks.")
            for level, title, page_num in bookmarks:
                toc_entries.append(TOCEntry(title=title, page_number=page_num, level=level))
    except Exception as e:
        logging.warning(f"Could not extract bookmarks from PDF: {e}")
    return toc_entries

def detect_toc_entries(pages_structured_text: List[List[Dict]], toc_page_limit=8) -> List[TOCEntry]:
    """Extracts Table of Contents entries from the first few pages using structured text."""
    toc_structured_lines = [line for page in pages_structured_text[:toc_page_limit] for line in page]

    # Calculate average font size for the TOC pages to identify larger headings
    all_font_sizes = [line['size'] for line in toc_structured_lines if line['size'] > 0]
    if not all_font_sizes:
        avg_font_size = 12.0 # Default if no font sizes found
    else:
        avg_font_size = sum(all_font_sizes) / len(all_font_sizes)

    large_font_threshold = avg_font_size * 1.1 # Slightly lower threshold for TOC entries

    entries = []
    toc_found_by_keyword = False
    toc_start_idx = -1

    # Reintroduce flexible keyword search for TOC
    toc_keywords = re.compile(r'ÍNDICE|INDEX|CONTENIDO|TABLA DE CONTENIDO|SUMARIO|CONTENTS|TABLE OF CONTENTS', re.IGNORECASE)
    for i, line_data in enumerate(toc_structured_lines):
        text = line_data['text'].strip()
        if toc_keywords.fullmatch(text):
            toc_start_idx = i
            toc_found_by_keyword = True
            break

    if toc_found_by_keyword:
        # If a TOC keyword is found, collect subsequent lines as entries
        # until a clear break (e.g., a blank line, or a line that looks like body text)

        # Calculate average font size of the *potential TOC entries* themselves
        potential_toc_entry_sizes = [line['size'] for line in toc_structured_lines[toc_start_idx + 1:] if line['size'] > 0]
        if potential_toc_entry_sizes:
            avg_toc_entry_size = sum(potential_toc_entry_sizes) / len(potential_toc_entry_sizes)
        else:
            avg_toc_entry_size = avg_font_size # Fallback to overall average if no entries yet

        # Heuristic for chapter/section prefixes and numbering
        chapter_prefix_pattern = re.compile(r"^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*", re.IGNORECASE)

        for i in range(toc_start_idx + 1, len(toc_structured_lines)):
            line_data = toc_structured_lines[i]
            text = line_data['text'].strip()

            if not text: # Stop on blank line
                break

            # Refined Heuristic to stop collecting TOC entries:
            # Stop if the line is excessively long (likely body text, not a title).
            # OR if the line's font size is significantly smaller than the average TOC entry size
            # AND it's not bold (indicating a new main heading/chapter start).
            if len(text.split()) > 20 or \
               (line_data.get('size', 0) < avg_toc_entry_size * 0.8 and not line_data.get('is_bold', False)): # Significantly smaller and not bold
                break

            # Try to extract chapter number and title
            match = chapter_prefix_pattern.match(text)
            if match:
                clean_label = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*', '', text, flags=re.IGNORECASE).strip()
                if clean_label:
                    entries.append(TOCEntry(title=clean_label, page_number=0)) # Page number will be determined later
                continue

            # If no chapter prefix, but it's a prominent line (bold or large font) and short
            if (line_data.get('is_bold', False) or line_data.get('size', 0) > large_font_threshold) and \
               1 < len(text.split()) < 10: # Short title
                clean_label = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*', '', text, flags=re.IGNORECASE).strip()
                if clean_label:
                    entries.append(TOCEntry(title=clean_label, page_number=0))
                continue

        if entries:
            print(f"Detected {len(entries)} entries from explicit TOC section.")
            return entries

    # Fallback to traditional TOC patterns if no explicit TOC keyword was found or it yielded no entries
    # Pattern for "Title ....... PageNum"
    toc_pattern_dots = re.compile(r"^(?P<label>.+?)\s*\.{3,}\s*(?P<page>\d+)\s*$", re.MULTILINE)

    # New pattern: A line that is short, potentially bold or larger font, and not ending in punctuation
    general_toc_title_pattern = re.compile(r"^[A-ZÁÉÍÓÚÑa-z\d\s'’,-]{2,50}$") # 2 to 50 characters, no ending punctuation

    for i, line_data in enumerate(toc_structured_lines):
        text = line_data['text'].strip()
        if not text: continue

        # First, try traditional patterns (dots or page numbers)
        match = toc_pattern_dots.match(text)
        if match:
            label = match.group('label').strip()
            page = int(match.group('page'))
            clean_label = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*', '', label, flags=re.IGNORECASE).strip()
            if clean_label:
                entries.append(TOCEntry(title=clean_label, page_number=page))
            continue

        # Try pattern without dots, but only if font is larger or bold AND it matches general title pattern
        if (line_data.get('is_bold', False) or line_data.get('size', 0) > large_font_threshold) and \
           general_toc_title_pattern.match(text):
            # We don't have a page number here, so assign 0 as placeholder
            clean_label = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*', '', text, flags=re.IGNORECASE).strip()
            if clean_label:
                entries.append(TOCEntry(title=clean_label, page_number=0))
            continue

    print(f"Detected {len(entries)} entries in the Table of Contents.")
    return entries
