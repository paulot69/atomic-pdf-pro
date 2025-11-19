import re
from typing import List, Dict
from .indice_detector import TOCEntry, _normalize_title
from ..limpieza.normalizador import normalize_text
from collections import Counter # ADDED: Import Counter for font size analysis

def _find_headers_with_toc(structured_lines: List[Dict], toc_entries: List[TOCEntry]) -> List[Dict]:
    """
    Finds chapter headers by performing a flexible, substring match of TOC entries against the document text.
    Returns a list of dictionaries, each containing the index, title, and crucially, the hierarchy level.
    """
    header_locations = []
    
    # Pre-normalize the TOC titles for efficient searching
    normalized_toc = [(entry, _normalize_title(entry.title)) for entry in toc_entries]

    # Use a set to avoid re-processing the same line index
    found_indices = set()

    for i, line_data in enumerate(structured_lines):
        if i in found_indices:
            continue

        line_text = line_data['text'].strip()
        if not line_text:
            continue

        normalized_line = _normalize_title(line_text)

        # Iterate through TOC entries to find a substring match
        for toc_entry, normalized_toc_title in normalized_toc:
            if normalized_toc_title in normalized_line:
                # Use the full line text from the PDF as the title, as it's more complete
                # and capture the level from the matched TOC entry.
                header_locations.append({
                    "idx": i,
                    "title": line_text,
                    "raw_title": line_text,
                    "level": toc_entry.level
                })
                found_indices.add(i)
                # Break to ensure we only match one TOC entry per line
                break

    print(f"Flexible TOC matching found {len(header_locations)} header(s).")
    return header_locations

def _find_headers_with_fallback(structured_lines: List[Dict]) -> List[dict]:
    """Fallback method to find chapters using generic patterns and font information."""
    header_locations = []
    
    # Calculate average font size for the document to identify larger headings
    all_font_sizes = [line['size'] for line in structured_lines if line['size'] > 0]
    if not all_font_sizes:
        avg_font_size = 12.0 # Default if no font sizes found
    else:
        avg_font_size = sum(all_font_sizes) / len(all_font_sizes)
    
    # Define a threshold for what constitutes a "large" font size
    # A heading is typically 1.2x to 1.5x larger than body text
    large_font_threshold = avg_font_size * 1.2 

    # Expanded patterns for chapter/section prefixes and numbering
    chapter_patterns = [
        re.compile(r"^\s*(Cap[ií]tulo|Chapter|Secci[oó]n|Section|Parte|Part)\s+([IVXLCDM\d]+)\b.*$", re.IGNORECASE),
        re.compile(r"^\s*(?P<num>\d+)\.\s*(?P<title>.+?)\s*$", re.IGNORECASE), # e.g., "1. Introduction"
        re.compile(r"^\s*(?P<num>[IVXLCDM]+)\.\s*(?P<title>.+?)\s*$", re.IGNORECASE), # e.g., "I. The Beginning"
    ]
    # Heuristic for short, uppercase lines without ending punctuation, surrounded by blank lines
    uppercase_pattern = re.compile(r"^[A-ZÁÉÍÓÚÑ\s'’,-]+$")

    for i, line_data in enumerate(structured_lines):
        stripped_text = line_data['text'].strip()
        if not stripped_text: continue

        # Heuristic 1: Chapter/Section prefixes and numbering (text-based)
        matched = False
        for pattern in chapter_patterns:
            match = pattern.match(stripped_text)
            if match:
                header_locations.append({"idx": i, "title": stripped_text, "raw_title": stripped_text})
                matched = True
                break
        if matched:
            continue

        # Heuristic 2: Isolated uppercase titles (text-based)
        is_surrounded_by_blanks = (i > 0 and not structured_lines[i-1]['text'].strip()) and \
                                  (i < len(structured_lines) - 1 and not structured_lines[i+1]['text'].strip())

        if (1 < len(stripped_text.split()) < 7 and uppercase_pattern.match(stripped_text) and is_surrounded_by_blanks):
             header_locations.append({"idx": i, "title": stripped_text, "raw_title": stripped_text})
             continue
        
        # Heuristic 3: Font-based detection (new)
        # Look for lines that are significantly larger or bold, and not too long
        if line_data['is_bold'] and line_data['size'] > large_font_threshold and \
           1 < len(stripped_text.split()) < 15 and not stripped_text.endswith(('.', '!', '?')):
            header_locations.append({"idx": i, "title": stripped_text, "raw_title": stripped_text})
            continue

        # Heuristic 4: Number/Roman numeral on one line, title on next (text-based, adapted)
        if re.fullmatch(r'\s*(\d+|[IVXLCDM]+)\s*', stripped_text) and i + 1 < len(structured_lines):
            next_line_data = structured_lines[i+1]
            next_line_text = next_line_data['text'].strip()
            if next_line_text and 1 < len(next_line_text.split()) < 10 and uppercase_pattern.match(next_line_text):
                header_locations.append({"idx": i, "title": next_line_text, "raw_title": f"{stripped_text}\n{next_line_text}"})
                # We don't increment i here, as the main loop will do it.
                # The next line will be processed as content of this header.
                pass

    print(f"Fallback detection found {len(header_locations)} potential chapter(s).")
    return header_locations

def split_into_chapters(pages_structured_text: List[List[Dict]], toc_entries: List[TOCEntry]) -> List[dict]:
    """Splits text into chapters, using TOC-based matching first and falling back to generic patterns."""
    # Flatten the structured text into a single list of structured lines
    all_structured_lines = [line for page in pages_structured_text for line in page]
    
    header_locations = []

    if toc_entries:
        # _find_headers_with_toc now expects structured lines
        header_locations = _find_headers_with_toc(all_structured_lines, toc_entries)

    if not header_locations:
        print("Warning: TOC-based detection failed. Using fallback method.")
        # _find_headers_with_fallback will now use structured lines
        header_locations = _find_headers_with_fallback(all_structured_lines)

    if not header_locations:
        print("No chapters detected. Treating the entire document as a single chapter.")
        full_text_content = normalize_text(all_structured_lines)
        return [{"number": 1, "title": "Contenido Completo", "kind": "chapter",
                 "sections": [{"title": "Contenido Completo", "content": full_text_content}]}]

    chapters = []
    chapter_number_counter = 1
    special_section_keywords = ["introducción", "prólogo", "epílogo", "conclusión", "apéndice"]

    for i, header in enumerate(header_locations):
        start_idx = header['idx'] + 1
        end_idx = header_locations[i + 1]['idx'] if i + 1 < len(header_locations) else len(all_structured_lines)
        
        # Extract content from structured lines
        chapter_structured_content = all_structured_lines[start_idx:end_idx]

        sections = split_chapter_into_sections(chapter_structured_content, header['title']) # Pass structured content

        kind = "special" if any(keyword in _normalize_title(header['title']) for keyword in special_section_keywords) else "chapter"

        # The level is now directly available in the header dictionary
        level = header.get('level', 1)

        chapter_data = {"title": header['title'], "raw_title": header['raw_title'], "kind": kind, "level": level, "sections": sections}
        if kind == "chapter":
            chapter_data["number"] = chapter_number_counter
            chapter_number_counter += 1

        chapters.append(chapter_data)

    print(f"Successfully split the document into {len(chapters)} main chapter(s)/section(s).")
    return chapters

def _get_dominant_style(structured_content: List[Dict]) -> (str, float, bool):
    """
    Determines the most common font style (font_name, size, is_bold) in a list of structured text lines.
    This is assumed to be the body text style.
    """
    if not structured_content:
        return "Arial", 12.0, False # Default fallback

    style_counter = Counter()
    for line in structured_content:
        # Heuristic: Consider lines with more than 3 words as body text to avoid titles skewing the result.
        if len(line['text'].split()) > 3:
            style_key = (line['font'], round(line['size']), line['is_bold'])
            style_counter[style_key] += 1

    if not style_counter:
        # If no lines match the heuristic, fall back to a simpler count
        for line in structured_content:
            style_key = (line['font'], round(line['size']), line['is_bold'])
            style_counter[style_key] += 1

    if not style_counter: # If still empty
        return "Arial", 12.0, False

    # The dominant style is the most frequent one
    dominant_style_key = style_counter.most_common(1)[0][0]
    return dominant_style_key[0], dominant_style_key[1], dominant_style_key[2]

def split_chapter_into_sections(chapter_structured_content: List[Dict], chapter_title: str) -> List[dict]:
    """
    Splits a chapter's content into sections based on a conservative, style-based subtitle detection.
    A line is considered a subtitle if its style is different from the dominant body text style
    and it meets certain structural criteria.
    """
    if not chapter_structured_content:
        return []

    # 1. Determine the dominant style of the body text for this chapter
    dom_font, dom_size, dom_bold = _get_dominant_style(chapter_structured_content)
    print(f"Chapter '{chapter_title[:30]}...': Dominant style: {dom_font}, {dom_size}pt, Bold={dom_bold}")

    sections = []
    section_breaks = []

    # 2. Iterate through lines to find potential subtitles
    for i, line_data in enumerate(chapter_structured_content):
        stripped_text = line_data['text'].strip()
        if not stripped_text:
            continue

        # --- Conservative Subtitle Heuristics ---
        is_subtitle = False
        
        # Style comparison
        line_font = line_data['font']
        line_size = round(line_data['size'])
        line_bold = line_data['is_bold']

        style_is_different = (line_font != dom_font or line_size != dom_size or line_bold != dom_bold)
        
        # Structural checks
        word_count = len(stripped_text.split())
        is_short = 1 <= word_count < 15
        ends_like_title = not stripped_text.endswith(('.', '?', '!', ':', ','))

        # A line is a subtitle if its style deviates and it looks like a title
        if style_is_different and is_short and ends_like_title:
            # Avoid single-word, all-caps lines which might be artifacts, unless they are significantly larger
            if word_count == 1 and stripped_text.isupper() and line_size <= dom_size * 1.2:
                continue

            is_subtitle = True
        
        if is_subtitle:
            section_breaks.append({"title": stripped_text, "idx": i})
            print(f"  -> Found potential subtitle: '{stripped_text}' (Style: {line_font}, {line_size}pt, Bold={line_bold})")

    # 3. Structure the chapter based on the found subtitles
    if not section_breaks:
        print("  -> No subtitles found. Treating chapter as a single note.")
        full_content_text = normalize_text(chapter_structured_content)
        return [{"title": chapter_title, "content": full_content_text}]

    print(f"  -> Splitting chapter into {len(section_breaks) + 1} sections based on subtitles.")
    
    sections = []
    last_idx = 0

    # The first section is the content before the first subtitle
    first_break_idx = section_breaks[0]['idx']
    content_before_first_break = normalize_text(chapter_structured_content[0:first_break_idx])
    if content_before_first_break.strip():
        sections.append({"title": chapter_title, "content": content_before_first_break})

    # Create a section for each subtitle found
    for i, break_info in enumerate(section_breaks):
        section_title = break_info['title']
        
        start_idx = break_info['idx'] + 1
        end_idx = section_breaks[i + 1]['idx'] if i + 1 < len(section_breaks) else len(chapter_structured_content)
        
        section_content_structured = chapter_structured_content[start_idx:end_idx]
        section_content_text = normalize_text(section_content_structured)
        
        if section_content_text.strip():
            sections.append({"title": section_title, "content": section_content_text})

    # Return only sections that have actual content
    return [s for s in sections if s.get('content', '').strip()]
