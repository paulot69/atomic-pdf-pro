import re

def _roman_to_int(s):
    """Converts a Roman numeral string to an integer."""
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i-1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i-1]]
        else:
            int_val += rom_val[s[i]]
    return int_val

def split_into_chapters(pages_text):
    """
    Splits the text into chapters based on predefined patterns.
    """
    full_text = "\n".join(pages_text)

    # Regex to find chapter titles (e.g., "Chapter 1", "CAPÍTULO I")
    chapter_regex = re.compile(
        r"^(Capítulo|CAPÍTULO|Chapter|CHAPTER)\s+([IVXLCDM]+|[0-9]+)",
        re.MULTILINE
    )

    matches = list(chapter_regex.finditer(full_text))

    if not matches:
        return [{
            "number": 1,
            "title": "Capítulo Único",
            "content": full_text.strip()
        }]

    chapters = []
    for i, match in enumerate(matches):
        # Determine chapter number
        num_str = match.group(2)
        if num_str.isdigit():
            chapter_number = int(num_str)
        else:
            chapter_number = _roman_to_int(num_str.upper())

        # Determine chapter content boundaries
        start_content = match.end()
        end_content = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)

        content = full_text[start_content:end_content].strip()

        chapters.append({
            "number": chapter_number,
            "title": f"Capítulo {chapter_number:02d}",
            "content": content
        })

    return chapters
