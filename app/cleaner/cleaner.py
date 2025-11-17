import re

def clean_section_text(section_content: str) -> str:
    """
    Cleans the text content of a single section.
    """
    # Sanitize for problematic characters first
    sanitized_content = section_content.encode('utf-8', 'ignore').decode('utf-8')

    # Remove lines that are only numbers (likely page numbers)
    lines = sanitized_content.split('\n')
    cleaned_lines = [line for line in lines if not re.fullmatch(r'\s*\d+\s*', line)]

    cleaned_text = "\n".join(cleaned_lines)

    # Normalize multiple empty lines into a single one
    cleaned_text = re.sub(r'(\n\s*){3,}', '\n\n', cleaned_text)

    return cleaned_text.strip()
