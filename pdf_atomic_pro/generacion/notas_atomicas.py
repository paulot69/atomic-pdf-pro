import os
import re
import yaml
from typing import List, Dict
from .yaml_builder import generate_frontmatter, _sanitize_title_for_filename

def _generate_navigation_footer(atomic_note: Dict, book_title: str) -> str:
    """Generates the standardized navigation footer for an atomic note."""
    # Sanitize titles for use in filenames and wikilinks
    chapter_title_sanitized = _sanitize_title_for_filename(atomic_note['chapter_title'])
    book_title_sanitized = _sanitize_title_for_filename(book_title)

    # MOC del Capítulo
    chapter_moc_filename_base = f"MOC---{chapter_title_sanitized}" # Use sanitized title
    if atomic_note['chapter_kind'] == 'chapter' and atomic_note['chapter_number'] is not None:
        chapter_folder_name = f"Capítulo-{atomic_note['chapter_number']:02d}---{chapter_title_sanitized}" # Use sanitized title
    else:
        chapter_folder_name = chapter_title_sanitized # Use sanitized title

    # Construct the wikilink target using sanitized names
    chapter_moc_link_target = f"{chapter_folder_name}/{chapter_moc_filename_base}"
    # The display text can still be the original title for readability
    chapter_moc_display_text = f"MOC - {atomic_note['chapter_title']}"

    # MOC principal del Libro
    book_moc_filename_base = f"MOC---{book_title_sanitized}" # Use sanitized title
    book_moc_display_text = f"MOC - {book_title}"

    footer = f"""---
#### _Ver otros conceptos en este capítulo_:

```dataviewjs
const currentFilePath = dv.current().file.path;
const currentFolderPath = currentFilePath.substring(0, currentFilePath.lastIndexOf("/"));
const pages = dv.pages(`"{{chapter_path_placeholder}}"`)  .where(p => p.file.path !== currentFilePath && !p.file.name.startsWith("MOC"))  .sort(p => p.file.name, 'asc');

const style = document.createElement("style");
style.textContent = `
.card {{ background-color: var(--background-secondary); border: 1px solid var(--background-modifier-border); padding: 14px 18px; border-radius: 8px; margin: 0 auto 12px auto; width: 100%; max-width: 700px; }}
.card-title {{ font-weight: 600; font-size: 1.3em; margin-bottom: 6px; text-align: left; }}
.card-title a {{ text-decoration: none !important; color: var(--text-accent) !important; display: inline-block; text-align: left; }}
.card-summary {{ font-size: 0.9em; color: var(--text-muted); text-align: left; }}
`;
document.head.appendChild(style);

for (const page of pages) {{
  const resumen = page.resumen || "Sin resumen disponible.";
  const card = document.createElement("div");
  card.className = "card";
  const title = document.createElement("div");
  title.className = "card-title";
  const link = document.createElement("a");
  link.href = page.file.path;
  link.textContent = page.file.name.replace(/\.md$/, '');
  link.className = "internal-link";
  link.setAttribute("data-href", page.file.path);
  title.appendChild(link);
  const summary = document.createElement("div");
  summary.textContent = resumen;
  card.appendChild(title);
  card.appendChild(summary);
  dv.container.appendChild(card);
}}
```

---
_Volver al [[{chapter_moc_link_target}|{chapter_moc_display_text}]]_
_Volver al [[{book_moc_filename_base}|{book_moc_display_text}]]_
"""

    return footer

def process_and_write_atomic_notes(chapters: List[Dict], book_title: str, author: str, year: int, book_root: str) -> List[Dict]:
    """
    Processes chapters into atomic notes and writes them to the vault.
    """
    atomic_chapters_data = []
    all_atomic_notes = []

    chapter_num_counter = 1
    for chapter in chapters:
        if chapter.get('kind') == 'chapter':
            current_chapter_number = chapter_num_counter
            chapter_num_counter += 1
        else:
            current_chapter_number = None

        atomic_notes_in_chapter = []
        note_num_counter = 1
        for section in chapter['sections']:
            atomic_note_title = section['title']
            atomic_note_content = section['content']

            if current_chapter_number is not None:
                decimal_number = f"{current_chapter_number}.{note_num_counter}"
            else:
                decimal_number = None

            atomic_note = {
                "chapter_title": chapter['title'],
                "chapter_number": current_chapter_number,
                "chapter_kind": chapter['kind'],
                "note_title": atomic_note_title,
                "note_decimal_number": decimal_number,
                "content": atomic_note_content,
            }

            atomic_note['frontmatter'] = generate_frontmatter(atomic_note, book_title, author)
            atomic_note['footer'] = _generate_navigation_footer(atomic_note, book_title)

            atomic_notes_in_chapter.append(atomic_note)
            all_atomic_notes.append(atomic_note)
            note_num_counter += 1

        atomic_chapters_data.append({
            "chapter_title": chapter['title'],
            "chapter_number": current_chapter_number,
            "chapter_kind": chapter['kind'],
            "atomic_notes": atomic_notes_in_chapter
        })

    # Create a mapping from note title to its full path for wikilinking
    note_path_mapping = {}
    for chapter_data in atomic_chapters_data:
        chapter_title = chapter_data['chapter_title']
        chapter_kind = chapter_data['chapter_kind']
        chapter_number = chapter_data['chapter_number']

        if chapter_kind == 'chapter' and chapter_number is not None:
            folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}"
        else:
            folder_name = _sanitize_title_for_filename(chapter_title)

        for atomic_note in chapter_data['atomic_notes']:
            note_title = atomic_note['note_title']
            note_decimal_number = atomic_note['note_decimal_number']

            if note_decimal_number:
                note_filename = f"{note_decimal_number} - {_sanitize_title_for_filename(note_title)}.md"
            else:
                note_filename = f"Nota - {_sanitize_title_for_filename(note_title)}.md"

            full_relative_path = os.path.join(folder_name, note_filename).replace('\\', '/')
            note_path_mapping[note_title] = full_relative_path
            if 'alias' in atomic_note['frontmatter']:
                for alias in atomic_note['frontmatter']['alias']:
                    note_path_mapping[alias] = full_relative_path

    # Perform wikilink replacement and write notes
    for chapter_data in atomic_chapters_data:
        chapter_title = chapter_data['chapter_title']
        chapter_kind = chapter_data['chapter_kind']
        chapter_number = chapter_data['chapter_number']

        if chapter_kind == 'chapter' and chapter_number is not None:
            folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}"
        else:
            folder_name = _sanitize_title_for_filename(chapter_title)

        chapter_path = os.path.join(book_root, folder_name)
        os.makedirs(chapter_path, exist_ok=True)

        for atomic_note in chapter_data['atomic_notes']:
            # Wikilink replacement
            for raw_target_title, sanitized_target_path in note_path_mapping.items():
                if raw_target_title == atomic_note['note_title']:
                    continue
                pattern = r'(?<!\[\[)(?:^|(?<=\W))(' + re.escape(raw_target_title) + r')(?:$|(?=\W))(?!\]\])'
                atomic_note['content'] = re.sub(pattern, rf'[[{sanitized_target_path}|\1]]', atomic_note['content'], flags=re.IGNORECASE)

            # Write the note
            note_title = atomic_note['note_title']
            note_decimal_number = atomic_note['note_decimal_number']
            if note_decimal_number:
                note_filename = f"{note_decimal_number} - {_sanitize_title_for_filename(note_title)}.md"
            else:
                note_filename = f"Nota - {_sanitize_title_for_filename(note_title)}.md"
            file_path = os.path.join(chapter_path, note_filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(atomic_note['frontmatter'], f, allow_unicode=True, sort_keys=False)
                f.write("---\n\n")
                f.write(f"# {note_title}\n\n")
                f.write(atomic_note['content'])
                footer_content = atomic_note['footer'].replace("{{chapter_path_placeholder}}", chapter_path.replace(book_root + os.sep, '').replace('\\', '/'))
                f.write(footer_content)

    return atomic_chapters_data
