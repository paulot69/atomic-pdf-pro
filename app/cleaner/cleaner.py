import re
from collections import Counter

def _identify_headers_and_footers(pages_text, threshold=0.5):
    """
    Identifies common headers and footers from a list of page texts.
    A line is considered a header/footer if it appears on more than `threshold` of the pages.
    """
    header_candidates = []
    footer_candidates = []

    for text in pages_text:
        lines = text.strip().split('\n')
        if len(lines) > 2:
            header_candidates.append(lines[0].strip())
            footer_candidates.append(lines[-1].strip())

    header_counts = Counter(line for line in header_candidates if line)
    footer_counts = Counter(line for line in footer_candidates if line)

    num_pages = len(pages_text)
    common_lines = set()

    for line, count in header_counts.items():
        if count / num_pages > threshold:
            common_lines.add(line)

    for line, count in footer_counts.items():
        if count / num_pages > threshold:
            common_lines.add(line)

    return common_lines

def clean_chapter_text(chapter_content, all_pages_text):
    """
    Cleans the text of a single chapter.
    """
    # 0. Sanitize for problematic characters
    sanitized_content = chapter_content.encode('utf-8', 'ignore').decode('utf-8')

    # 1. Identify and remove common headers/footers
    common_lines = _identify_headers_and_footers(all_pages_text)
    cleaned_lines = []
    for line in sanitized_content.split('\n'):
        stripped_line = line.strip()
        if stripped_line not in common_lines and not re.fullmatch(r'\d+', stripped_line):
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)

    # 2. Remove remaining loose page numbers (often at start/end of lines)
    cleaned_text = re.sub(r'^\s*\d+\s*|\s*\d+\s*$', '', cleaned_text, flags=re.MULTILINE)

    # 3. Remove duplicate empty lines
    cleaned_text = re.sub(r'(\n\s*){3,}', '\n\n', cleaned_text)

    return cleaned_text.strip()
