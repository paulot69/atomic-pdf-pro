import re
from typing import List, Dict
from .indice_detector import TOCEntry, _normalize_title
from ..limpieza.normalizador import normalize_text
from collections import Counter # ADDED: Import Counter for font size analysis

def _find_headers_with_toc(all_structured_lines: List[Dict], toc_entries: List[TOCEntry]) -> List[Dict]:
    """
    Finds chapter headers by performing page-aware matching of TOC entries against the document text.
    Prioritizes matches near the TOC entry's specified page number.
    Returns a list of dictionaries, each containing the index, title, raw_title, and level.
    """
    header_locations = []
    
    # Sort toc_entries by page_number to process sequentially
    sorted_toc_entries = sorted(toc_entries, key=lambda x: x.page_number)
    
    matched_toc_entries_indices = set() # To ensure each TOC entry is used once
    
    # Iterate through sorted TOC entries
    for toc_idx, toc_entry in enumerate(sorted_toc_entries):
        # We search for a line corresponding to this TOC entry.
        # Prioritize search around the page number specified in the TOC.
        # Allow for a small page tolerance (e.g., +/- 1 page) for flexibility.
        
        # Calculate start and end indices in all_structured_lines for the page range
        # Assume an average of 50 lines per page for estimation, this is very rough
        # A more precise method would involve building an index of first_line_idx_for_page
        
        # For a simple first pass, let's just iterate through the structured lines
        # and prioritize by distance to the target page.

        best_match_idx = -1
        smallest_distance = float('inf')
        
        normalized_toc_title = _normalize_title(toc_entry.title)
        
        # Search window: check lines on the target page, and a few pages before/after.
        # Find the approximate start line for the toc_entry.page_number
        target_page_start_line_idx = -1
        for i, line_data in enumerate(all_structured_lines):
            if line_data['original_page_number'] == toc_entry.page_number:
                target_page_start_line_idx = i
                break
        
        search_start_idx = max(0, target_page_start_line_idx - 100) # Look back a couple of pages
        search_end_idx = min(len(all_structured_lines), target_page_start_line_idx + 200) # Look forward a few pages


        for i in range(search_start_idx, search_end_idx):
            line_data = all_structured_lines[i]
            line_text = line_data['text'].strip()
            if not line_text:
                continue
            
            normalized_line = _normalize_title(line_text)
            
            # --- Matching Criteria ---
            # 1. Exact match for the cleaned title
            # 2. Line text starts with the cleaned title (to handle "Title: Subtitle" cases)
            # 3. Substring match, but give it lower priority
            
            match_score = 0
            if normalized_line == normalized_toc_title:
                match_score = 3
            elif normalized_line.startswith(normalized_toc_title):
                match_score = 2
            elif normalized_toc_title in normalized_line:
                match_score = 1
            
            if match_score > 0:
                current_distance = abs(line_data['original_page_number'] - toc_entry.page_number)
                
                # If we find a good match (exact or starts with) on the target page, it's strong.
                if match_score >= 2 and current_distance == 0:
                    best_match_idx = i
                    break # Found a very strong match, stop searching for this TOC entry
                
                # Otherwise, keep track of the best match by smallest page distance
                if current_distance < smallest_distance:
                    smallest_distance = current_distance
                    best_match_idx = i
        
        if best_match_idx != -1:
            line_data = all_structured_lines[best_match_idx]
            header_locations.append({
                "idx": best_match_idx,
                "title": line_data['text'], # The title as it appears in the document
                "raw_title": toc_entry.raw_title, # The original TOC entry text
                "level": toc_entry.level,
                "original_page_number": line_data['original_page_number']
            })
            matched_toc_entries_indices.add(toc_idx)

    # Sort the found headers by their index in the document
    header_locations.sort(key=lambda x: x['idx'])

    # Filter out duplicate entries if the same line matches multiple TOC entries
    # (This shouldn't happen with `break` but as a safeguard)
    unique_header_locations = []
    seen_indices = set()
    for header in header_locations:
        if header['idx'] not in seen_indices:
            unique_header_locations.append(header)
            seen_indices.add(header['idx'])
    
    print(f"Page-aware TOC matching found {len(unique_header_locations)} header(s).")
    return unique_header_locations

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

def split_into_chapters(pages_structured_text: List[List[Dict]], toc_entries: List[TOCEntry], config: Dict) -> List[dict]:
    """Splits text into chapters, using TOC-based matching first and falling back to generic patterns."""
    # Flatten the structured text into a single list of structured lines,
    # augmenting each line with its original page number.
    all_structured_lines = []
    for page_num, page in enumerate(pages_structured_text):
        for line in page:
            line_with_page = line.copy()
            line_with_page['original_page_number'] = page_num + 1 # Convert to 1-based index
            all_structured_lines.append(line_with_page)
    
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
    special_section_keywords = ["introducción", "prólogo", "prólogo", "epílogo", "conclusión", "apéndice"]

    for i, header in enumerate(header_locations):
        start_idx = header['idx'] + 1
        end_idx = header_locations[i + 1]['idx'] if i + 1 < len(header_locations) else len(all_structured_lines)
        
        # Extract content from structured lines
        chapter_structured_content = all_structured_lines[start_idx:end_idx]

        sections = split_chapter_into_sections(chapter_structured_content, header['title'], config) # Pass config


        kind = "special" if any(keyword in _normalize_title(header['title']) for keyword in special_section_keywords) else "chapter"

        # The level is now directly available in the header dictionary
        level = header.get('level', 1)

        chapter_data = {"title": header['title'].strip(), "raw_title": header['raw_title'], "kind": kind, "level": level, "sections": sections}
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
        if line['text'].strip(): # Only consider non-empty lines
            style_key = (line['font'], round(line['size']), line['is_bold'])
            style_counter[style_key] += 1

    if not style_counter:
        # If still empty (e.g., all lines were empty), fall back to default
        return "Arial", 12.0, False

    # The dominant style is the most frequent one
    dominant_style_key = style_counter.most_common(1)[0][0]
    return dominant_style_key[0], dominant_style_key[1], dominant_style_key[2]

def split_chapter_into_sections(chapter_structured_content: List[Dict], chapter_title: str, config: Dict) -> List[dict]:
    """
    Splits a chapter's content into sections based on a configurable, score-based subtitle detection.
    Heuristics and thresholds are loaded from the provided configuration object.
    """
    if not chapter_structured_content:
        return []

    # 1. Use configuration for subtitle detection (passed as argument)
    try:
        detection_rules = config['subtitle_detection']
        heuristics = detection_rules['heuristics']
        threshold = detection_rules['threshold']
        numbering_pattern = re.compile(heuristics['numbering_pattern']['regex'], re.IGNORECASE)
    except (KeyError) as e:
        print(f"Warning: Missing or invalid subtitle detection config: {e}. Using default fallback logic.")
        # Provide a minimal fallback if config is missing/broken
        heuristics = {
            'bold_vs_not_bold': {'score': 2},
            'font_size_increase_strong': {'multiplier': 1.15, 'score': 2},
            'font_size_increase_weak': {'multiplier': 1.05, 'score': 1},
            'is_short': {'score': 1},
            'ends_like_title': {'score': 1},
            'numbering_pattern': {'score': 2, 'regex': r"^\s*(\d+(\.\d+)*|[a-zA-Z]\)|[ivxlcdm]+\.)\s+.*"}
        }
        threshold = 3
        numbering_pattern = re.compile(heuristics['numbering_pattern']['regex'], re.IGNORECASE)


    # 2. Determine the dominant style of the body text for this chapter
    dom_font, dom_size, dom_bold = _get_dominant_style(chapter_structured_content)
    print(f"Chapter '{chapter_title[:30]}...': Dominant style: {dom_font}, {dom_size}pt, Bold={dom_bold}")

    sections = []
    section_breaks = []

    # 3. Iterate through lines to find potential subtitles using the configured scoring system
    for i, line_data in enumerate(chapter_structured_content):
        stripped_text = line_data['text'].strip()
        if not stripped_text:
            continue

        score = 0
        line_size = round(line_data['size'])
        line_bold = line_data['is_bold']
        
        # Apply heuristics from config
        if line_bold and not dom_bold:
            score += heuristics['bold_vs_not_bold']['score']
        
        if line_size > dom_size * heuristics['font_size_increase_strong']['multiplier']:
            score += heuristics['font_size_increase_strong']['score']
        elif 'font_size_increase_weak' in heuristics and line_size > dom_size * heuristics['font_size_increase_weak']['multiplier']:
            score += heuristics['font_size_increase_weak']['score']

        word_count = len(stripped_text.split())
        if 1 <= word_count < 15: # is_short check
            score += heuristics['is_short']['score']
        if not stripped_text.endswith(('.', '?', '!', ':', ',')): # ends_like_title check
            score += heuristics['ends_like_title']['score']
            
        if numbering_pattern.match(stripped_text):
            score += heuristics['numbering_pattern']['score']

        if score >= threshold:
            if word_count == 1 and stripped_text.isupper() and line_size <= dom_size * 1.2:
                continue
            section_breaks.append({"title": stripped_text, "idx": i})
            print(f"  -> Found potential subtitle (Score: {score}): '{stripped_text}'")

    # 4. Structure the chapter based on the found subtitles
    if not section_breaks:
        print("  -> No subtitles found. Treating chapter as a single note.")
        full_content_text = normalize_text(chapter_structured_content)
        return [{"title": chapter_title, "content": full_content_text}]

    print(f"  -> Splitting chapter into {len(section_breaks) + 1} sections based on subtitles.")
    
    sections = []
    
    first_break_idx = section_breaks[0]['idx']
    content_before_first_break = normalize_text(chapter_structured_content[0:first_break_idx])
    if content_before_first_break.strip():
        sections.append({"title": chapter_title, "content": content_before_first_break})

    for i, break_info in enumerate(section_breaks):
        section_title = break_info['title']
        start_idx = break_info['idx'] + 1
        end_idx = section_breaks[i + 1]['idx'] if i + 1 < len(section_breaks) else len(chapter_structured_content)
        
        section_content_structured = chapter_structured_content[start_idx:end_idx]
        section_content_text = normalize_text(section_content_structured)
        
        if section_content_text.strip():
            sections.append({"title": section_title, "content": section_content_text})

    return [s for s in sections if s.get('content', '').strip()]
