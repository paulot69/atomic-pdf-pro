import re

def generate_summary(text_content: str, max_length: int = 250) -> str:
    """
    Generates a brief summary for a block of text.

    NOTE FOR JULES: This is a placeholder implementation. The current logic simply
    takes the first sentence of the text. You should replace this logic
    with a call to your own language generation capabilities to create a high-quality,
    one-sentence summary of the provided `text_content`.
    The summary should be concise and capture the core concept of the note.
    """
    if not text_content:
        return ""

    # Find the first sentence (ends with a period, question mark, or exclamation point)
    match = re.search(r'([^.!?]+[.!?])', text_content)

    if match:
        summary = match.group(1).strip()
    else:
        # Fallback if no sentence-ending punctuation is found
        summary = text_content.strip()

    # Truncate if too long and add ellipsis
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + "..."

    return summary
