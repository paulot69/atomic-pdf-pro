import re

def _roman_to_int(s):
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
    Splits the text into chapters by detecting headers for chapters and special sections.
    """
    full_text = "\n".join(pages_text)
    lines = full_text.splitlines()

    chapter_patterns = [
        r'^\s*(Cap[ií]tulo|Chapter)\s+(\d+)\b.*$',
        r'^\s*(CAP[IÍ]TULO|CHAPTER)\s+(\d+)\b.*$',
        r'^\s*(Cap\.)\s+(\d+)\b.*$',
        r'^\s*(Cap[ií]tulo|Chapter)\s+([IVXLCDM]+)\b.*$',
    ]

    special_sections = [
        r'^\s*Pr[oó]logo\b.*$',
        r'^\s*Introducci[oó]n\b.*$',
        r'^\s*Ep[ií]logo\b.*$',
        r'^\s*Conclusi[oó]n\b.*$',
        r'^\s*Ap[eé]ndice\b.*$',
    ]

    headers = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check for numbered chapters
        is_chapter = False
        for pat in chapter_patterns:
            m = re.match(pat, stripped, re.IGNORECASE)
            if m:
                headers.append({
                    "idx": idx,
                    "kind": "chapter",
                    "raw_title": stripped,
                    "number_token": m.group(2),
                })
                is_chapter = True
                break
        if is_chapter:
            continue

        # Check for special sections
        for pat in special_sections:
            if re.match(pat, stripped, re.IGNORECASE):
                headers.append({
                    "idx": idx,
                    "kind": "section",
                    "raw_title": stripped,
                })
                break

    if not headers:
        return [{
            "type": "chapter",
            "number": 1,
            "title": "Capítulo Único",
            "content": full_text
        }]

    headers.sort(key=lambda h: h['idx'])

    chapters = []
    current_chapter_number = 1
    for i, h in enumerate(headers):
        start = h["idx"]
        end = headers[i + 1]["idx"] if i + 1 < len(headers) else len(lines)
        body_lines = lines[start + 1:end]
        content = "\n".join(body_lines).strip()

        if h["kind"] == "chapter":
            chapters.append({
                "type": "chapter",
                "number": current_chapter_number,
                "title": h["raw_title"],
                "content": content,
            })
            current_chapter_number += 1
        else: # kind == "section"
            chapters.append({
                "type": "section",
                "number": None,
                "title": h["raw_title"],
                "content": content,
            })

    n_chapters = sum(1 for c in chapters if c["type"] == "chapter")
    n_sections = sum(1 for c in chapters if c["type"] == "section")
    print(f"Found {n_chapters} chapter(s) and {n_sections} extra section(s).")

    return chapters
