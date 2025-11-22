from typing import Dict, List
from .utils import _sanitize_title_for_filename

def generate_frontmatter(atomic_note: Dict, book_title: str, author: str, thematic_folder: str = None, theme_nomenclature: str = None, summary: str = "", semantic_tags: List[str] = None) -> Dict:
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

    # Add semantic tags from AI
    if semantic_tags:
        tags.extend(semantic_tags)

    frontmatter = {
        "tags": tags,
        "resumen": summary,
        "alias": [atomic_note['note_title']]
    }
    return frontmatter
