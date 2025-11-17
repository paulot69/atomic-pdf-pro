import re
from dataclasses import dataclass
from typing import List
from unidecode import unidecode

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

def detect_toc_entries(pages_text: List[str], toc_page_limit=8) -> List[TOCEntry]:
    """Extracts Table of Contents entries from the first few pages."""
    toc_text = "\n".join(pages_text[:toc_page_limit])
    entries = []
    toc_pattern = re.compile(r"^(?P<label>.+?)\s*\.{3,}\s*(?P<page>\d+)\s*$", re.MULTILINE)

    for match in toc_pattern.finditer(toc_text):
        label = match.group('label').strip()
        page = int(match.group('page'))
        clean_label = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)[:.\s-]*', '', label, flags=re.IGNORECASE).strip()
        if clean_label:
            entries.append(TOCEntry(title=clean_label, page_number=page))

    print(f"Detected {len(entries)} entries in the Table of Contents.")
    return entries

def split_chapter_into_sections(chapter_content: str, chapter_title: str) -> List[dict]:
    """Splits a chapter's content into sections based on internal subtitles."""
    lines = chapter_content.split('\n')
    sections = []
    subtitle_pattern = re.compile(r"^(?![a-z\d\s]*$)[A-ZÁÉÍÓÚÑa-z\d\s'’,-]{1,100}$")
    section_breaks = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped: continue
        is_surrounded_by_blanks = (i > 0 and not lines[i-1].strip()) or (i < len(lines) - 1 and not lines[i+1].strip())
        if 1 < len(stripped.split()) < 10 and subtitle_pattern.match(stripped) and is_surrounded_by_blanks:
             section_breaks.append({"title": stripped, "idx": i})

    if not section_breaks:
        return [{"title": chapter_title, "content": chapter_content}]

    sections.append({"title": chapter_title, "content": "\n".join(lines[:section_breaks[0]['idx']]).strip()})
    for i, break_info in enumerate(section_breaks):
        start = break_info['idx'] + 1
        end = section_breaks[i + 1]['idx'] if i + 1 < len(section_breaks) else len(lines)
        sections.append({"title": break_info['title'], "content": "\n".join(lines[start:end]).strip()})

    return [s for s in sections if s['content']]

def _find_headers_with_toc(lines: List[str], toc_entries: List[TOCEntry]) -> List[dict]:
    """Finds chapter headers in text that match TOC entries."""
    toc_titles_norm = {_normalize_title(e.title) for e in toc_entries}
    header_locations = []

    patterns = {
        'single_line_numbered': re.compile(r"^\s*(?P<num>\d+)\s+(?P<title>[A-ZÁÉÍÓÚÑ].+?)\s*$"),
        'single_line_chapter_prefix': re.compile(r"^\s*Cap[ií]tulo\s+(?P<num>\d+|[IVXLCDM]+)\s*[:.-]?\s*(?P<title>.+?)\s*$", re.IGNORECASE),
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        matched = False
        for key, pattern in patterns.items():
            match = pattern.match(line)
            if match:
                title = match.group('title')
                if _normalize_title(title) in toc_titles_norm:
                    header_locations.append({"idx": i, "title": title, "raw_title": line})
                    matched = True
                    break
        if matched:
            i += 1
            continue

        if re.fullmatch(r'\s*\d+\s*', line) and i + 1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line and _normalize_title(next_line) in toc_titles_norm:
                header_locations.append({"idx": i, "title": next_line, "raw_title": f"{line}\n{next_line}"})
                i += 2
                continue

        i += 1

    return header_locations

def _find_headers_with_fallback(lines: List[str]) -> List[dict]:
    """Fallback method to find chapters using generic patterns."""
    header_locations = []
    # Pattern for "Chapter X", "Capítulo 1", etc.
    chapter_prefix_pattern = re.compile(r"^\s*(Cap[ií]tulo|Chapter)\s+([IVXLCDM\d]+)\b.*$", re.IGNORECASE)
    # Heuristic for short, uppercase lines without ending punctuation, surrounded by blank lines
    uppercase_pattern = re.compile(r"^[A-ZÁÉÍÓÚÑ\s'’,-]+$")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped: continue

        # Heuristic 1: Chapter prefixes
        match = chapter_prefix_pattern.match(stripped)
        if match:
            header_locations.append({"idx": i, "title": stripped, "raw_title": stripped})
            continue

        # Heuristic 2: Isolated uppercase titles
        is_surrounded_by_blanks = (i > 0 and not lines[i-1].strip()) and \
                                  (i < len(lines) - 1 and not lines[i+1].strip())

        if (1 < len(stripped.split()) < 7 and uppercase_pattern.match(stripped) and is_surrounded_by_blanks):
             header_locations.append({"idx": i, "title": stripped, "raw_title": stripped})

    print(f"Fallback detection found {len(header_locations)} potential chapter(s).")
    return header_locations

def split_into_chapters(pages_text: List[str]) -> List[dict]:
    """Splits text into chapters, using TOC-based matching first and falling back to generic patterns."""
    toc_entries = detect_toc_entries(pages_text)
    full_text = "\n".join(pages_text)
    lines = full_text.splitlines()
    header_locations = []

    if toc_entries:
        header_locations = _find_headers_with_toc(lines, toc_entries)

    if not header_locations:
        print("Warning: TOC-based detection failed. Using fallback method.")
        header_locations = _find_headers_with_fallback(lines)

    if not header_locations:
        print("No chapters detected. Treating the entire document as a single chapter.")
        return [{"number": 1, "title": "Contenido Completo", "kind": "chapter",
                 "sections": [{"title": "Contenido Completo", "content": full_text}]}]

    chapters = []
    chapter_number_counter = 1
    special_section_keywords = ["introducción", "prólogo", "epílogo", "conclusión", "apéndice"]

    for i, header in enumerate(header_locations):
        start = header['idx'] + 1
        end = header_locations[i + 1]['idx'] if i + 1 < len(header_locations) else len(lines)
        content = "\n".join(lines[start:end]).strip()

        kind = "special" if any(keyword in _normalize_title(header['title']) for keyword in special_section_keywords) else "chapter"
        sections = split_chapter_into_sections(content, header['title'])

        chapter_data = {"title": header['title'], "raw_title": header['raw_title'], "kind": kind, "sections": sections}
        if kind == "chapter":
            chapter_data["number"] = chapter_number_counter
            chapter_number_counter += 1

        chapters.append(chapter_data)

    print(f"Successfully split the document into {len(chapters)} main chapter(s)/section(s).")
    return chapters
