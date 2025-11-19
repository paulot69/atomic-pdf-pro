import re
from typing import List, Dict
from .indice_detector import TOCEntry, _normalize_title
from ..limpieza.normalizador import normalize_text
from collections import Counter # ADDED: Import Counter for font size analysis

def _find_headers_with_toc(structured_lines: List[Dict], toc_entries: List[TOCEntry]) -> List[dict]:
    """Finds chapter headers in structured text that match TOC entries, using font info."""
    toc_titles_norm = {_normalize_title(e.title) for e in toc_entries}
    header_locations = []

    # Calculate average font size for the document to identify larger headings
    all_font_sizes = [line['size'] for line in structured_lines if line['size'] > 0]
    if not all_font_sizes:
        avg_font_size = 12.0 # Default if no font sizes found
    else:
        avg_font_size = sum(all_font_sizes) / len(all_font_sizes)
    
    large_font_threshold = avg_font_size * 1.2 

    patterns = {
        'single_line_numbered': re.compile(r"^\s*(?P<num>\d+)\s+(?P<title>[A-ZÁÉÍÓÚÑ].+?)\s*$"),
        'single_line_chapter_prefix': re.compile(r"^\s*Cap[ií]tulo\s+(?P<num>\d+|[IVXLCDM]+)\s*[:.-]?\s*(?P<title>.+?)\s*$", re.IGNORECASE),
    }

    i = 0
    while i < len(structured_lines):
        line_data = structured_lines[i]
        line_text = line_data['text'].strip()
        if not line_text:
            i += 1
            continue

        matched = False
        for key, pattern in patterns.items():
            match = pattern.match(line_text)
            if match:
                title = match.group('title')
                if _normalize_title(title) in toc_titles_norm:
                    header_locations.append({"idx": i, "title": title, "raw_title": line_text})
                    matched = True
                    break
        if matched:
            i += 1
            continue

        # Also consider font-based matching for TOC entries
        if (line_data['is_bold'] or line_data['size'] > large_font_threshold) and \
           _normalize_title(line_text) in toc_titles_norm:
            header_locations.append({"idx": i, "title": line_text, "raw_title": line_text})
            i += 1
            continue

        if re.fullmatch(r'\s*\d+\s*', line_text) and i + 1 < len(structured_lines):
            next_line_data = structured_lines[i+1]
            next_line_text = next_line_data['text'].strip()
            if next_line_text and _normalize_title(next_line_text) in toc_titles_norm:
                header_locations.append({"idx": i, "title": next_line_text, "raw_title": f"{line_text}\n{next_line_text}"})
                i += 2
                continue

        i += 1

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

        chapter_data = {"title": header['title'], "raw_title": header['raw_title'], "kind": kind, "sections": sections}
        if kind == "chapter":
            chapter_data["number"] = chapter_number_counter
            chapter_number_counter += 1

        chapters.append(chapter_data)

    print(f"Successfully split the document into {len(chapters)} main chapter(s)/section(s).")
    return chapters

def split_chapter_into_sections(chapter_structured_content: List[Dict], chapter_title: str) -> List[dict]:
    """Splits a chapter's structured content into sections based on internal subtitles and font information."""
    if not chapter_structured_content:
        return []

    sections = []
    section_breaks = []

    # Calculate average font size of the chapter's body text for comparison
    # Exclude very large fonts which might be titles themselves, skewing the average
    font_sizes = [line['size'] for line in chapter_structured_content if line['size'] > 0 and len(line['text'].split()) > 5]
    if not font_sizes:
        # If no lines are long enough, use all available sizes
        font_sizes = [line['size'] for line in chapter_structured_content if line['size'] > 0]
    
    if not font_sizes:
        avg_body_font_size = 10.0 # A reasonable default
    else:
        # Use the most common font size as the body text size
        avg_body_font_size = Counter(font_sizes).most_common(1)[0][0]

    # A subtitle is slightly larger than the body text.
    subtitle_font_threshold = avg_body_font_size + 0.5 

    print(f"Chapter '{chapter_title[:30]}...': Avg body font size: {avg_body_font_size:.2f}, Subtitle threshold: {subtitle_font_threshold:.2f}")

    for i, line_data in enumerate(chapter_structured_content):
        stripped_text = line_data['text'].strip()
        if not stripped_text:
            continue

        # --- More Lenient Subtitle Heuristics ---
        is_subtitle = False
        word_count = len(stripped_text.split())
        
        # Condition 1: Text is bold and is short (like a title)
        is_bold_and_short = line_data['is_bold'] and (1 <= word_count < 15)
        
        # Condition 2: Text is noticeably larger and is short
        is_larger_and_short = line_data['size'] >= subtitle_font_threshold and (1 <= word_count < 15)

        # A line is a subtitle if it meets either condition, and doesn't look like a normal sentence
        if (is_bold_and_short or is_larger_and_short) and not stripped_text.endswith(('.', '?', '!')):
             # Additional check: ensure it's not just a few capitalized words in a sentence.
             # A simple check is to see if it starts with an uppercase letter.
            if stripped_text[0].isupper():
                is_subtitle = True
        
        if is_subtitle:
            section_breaks.append({"title": stripped_text, "idx": i})
            print(f"  -> Found potential subtitle: '{stripped_text}'")

    # If no subtitles were found, the whole chapter is one section.
    if not section_breaks:
        print("  -> No subtitles found. Treating chapter as a single note.")
        full_content_text = normalize_text(chapter_structured_content)
        return [{"title": chapter_title, "content": full_content_text}]

    # If subtitles were found, split the content accordingly.
    print(f"  -> Splitting chapter into {len(section_breaks) + 1} sections based on subtitles.")
    
    # 1. Content before the first subtitle (uses the main chapter title)
    content_before_first_break = normalize_text(chapter_structured_content[:section_breaks[0]['idx']])
    if content_before_first_break:
        sections.append({"title": chapter_title, "content": content_before_first_break})

    # 2. Content for each subtitle
    for i, break_info in enumerate(section_breaks):
        start_idx = break_info['idx']
        
        # The content for this section starts AFTER the subtitle line
        content_start_idx = start_idx + 1
        
        # The content ends right before the NEXT subtitle line
        content_end_idx = section_breaks[i + 1]['idx'] if i + 1 < len(section_breaks) else len(chapter_structured_content)
        
        section_content_structured = chapter_structured_content[content_start_idx:content_end_idx]
        section_content_text = normalize_text(section_content_structured)
        
        # The title is the subtitle line itself, plus any following subtitle-like lines
        section_title = chapter_structured_content[start_idx]['text']
        
        if section_content_text:
            sections.append({"title": section_title, "content": section_content_text})

    return [s for s in sections if s.get('content')]
