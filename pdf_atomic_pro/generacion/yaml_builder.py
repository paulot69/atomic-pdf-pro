import re
from typing import Dict, List
from collections import Counter

def _sanitize_title_for_filename(title: str, max_length: int = 100) -> str:
    """
    Sanitizes a title to be used in a filename, removing invalid characters,
    replacing spaces with hyphens, and limiting the length.
    """
    # Remove invalid characters for filenames
    title = re.sub(r'[\\/*?:"<>|«»()\[\]{}.,;!@#$%^&+=~`]', '', title)
    # Replace multiple spaces with a single space, then replace spaces with hyphens
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace(' ', '-')
    # Remove any leading/trailing hyphens
    title = title.strip('-')
    # Limit length
    if len(title) > max_length:
        title = title[:max_length].rsplit('-', 1)[0] # Try to cut at a hyphen
        if not title: # If cutting at hyphen resulted in empty string, just truncate
            title = title[:max_length]
    return title

def _generate_semantic_tags(content: str, max_tags: int = 3) -> List[str]:
    """
    Generates semantic tags from the content using a simple frequency analysis.
    """
    words = re.findall(r'\b\w+\b', content.lower())
    # A simple list of stopwords, you can expand this list
    stopwords = set(["de", "la", "el", "en", "y", "a", "los", "del", "las", "un", "por", "con", "no", "una", "su", "para", "es", "al", "lo", "como", "más", "o", "pero", "sus", "le", "ha", "me", "si", "sin", "sobre", "este", "ya", "entre", "cuando", "muy", "también", "hasta", "hay", "qué", "desde", "yo", "era", "uno", "él", "eso", "esa", "ese", "sí", "son", "fue", "ser", "mis", "había"])

    # Filter out stopwords and short words
    meaningful_words = [word for word in words if word not in stopwords and len(word) > 3]

    # Get the most common words
    word_counts = Counter(meaningful_words)
    most_common_words = word_counts.most_common(max_tags)

    return [word for word, count in most_common_words]

def generate_frontmatter(atomic_note: Dict, book_title: str, author: str) -> Dict:
    """Generates the YAML frontmatter for an atomic note."""

    # Structural tags
    tags = [
        f"libro/{_sanitize_title_for_filename(book_title).lower()}",
        f"capitulo/{_sanitize_title_for_filename(atomic_note['chapter_title']).lower()}"
    ]

    # Semantic tags
    semantic_tags = _generate_semantic_tags(atomic_note['content'])
    if semantic_tags:
        tags.extend(semantic_tags)

    frontmatter = {
        "tags": tags,
        "resumen": "", # Placeholder
        "alias": [atomic_note['note_title']]
    }
    return frontmatter
