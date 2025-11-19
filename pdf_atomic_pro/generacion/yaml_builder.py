import re
from typing import Dict, List
from collections import Counter
from .utils import _sanitize_title_for_filename

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

def generate_frontmatter(atomic_note: Dict, book_title: str, author: str, thematic_folder: str = None, theme_nomenclature: str = None, summary: str = "") -> Dict:
    """Generates the YAML frontmatter for an atomic note, including inferred domain tags and summary."""

    # Domain tag inference
    if thematic_folder and theme_nomenclature:
        domain = _sanitize_title_for_filename(thematic_folder).lower()
        sub_domain = _sanitize_title_for_filename(theme_nomenclature).lower()
        domain_tag = f"{domain}/{sub_domain}"
    else:
        domain_tag = "dominio/pendiente"

    # Structural tags
    tags = [
        domain_tag,
        f"libro/{_sanitize_title_for_filename(book_title).lower()}",
        f"capitulo/{_sanitize_title_for_filename(atomic_note['chapter_title']).lower()}"
    ]

    # Semantic tags
    semantic_tags = _generate_semantic_tags(atomic_note['content'])
    if semantic_tags:
        tags.extend(semantic_tags)

    frontmatter = {
        "tags": tags,
        "resumen": summary,
        "alias": [atomic_note['note_title']]
    }
    return frontmatter
