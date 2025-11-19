import os
import re
import yaml
from typing import List, Dict
from .utils import _sanitize_title_for_filename, get_main_moc_name
from .yaml_builder import generate_frontmatter

def _generate_navigation_footer(atomic_note: Dict, book_title: str) -> str:
    """Generates the standardized navigation footer for an atomic note."""
    author = atomic_note.get('author', 'Unknown')
    year = atomic_note.get('year', '0000')

    # Chapter MOC Link
    chapter_title_sanitized = _sanitize_title_for_filename(atomic_note['chapter_title'])
    if atomic_note.get('chapter_number') is not None:
        folder_name = f"Capítulo {atomic_note['chapter_number']:02d} - {chapter_title_sanitized}"
    else:
        folder_name = chapter_title_sanitized
    
    chapter_moc_filename = f"MOC - {chapter_title_sanitized}.md"
    chapter_moc_link_target = f"{folder_name}/{chapter_moc_filename}".replace("\", "/")
    chapter_moc_display_text = f"MOC - {atomic_note['chapter_title']}"

    # Main Book MOC Link
    main_moc_filename, _ = get_main_moc_name(book_title, author, year)
    main_moc_display_text = f"MOC - {book_title}"

    # Unindented DataviewJS script
    dataview_script = """```dataviewjs
const currentFilePath = dv.current().file.path;
const currentFolderPath = currentFilePath.substring(0, currentFilePath.lastIndexOf("/"));
const pages = dv.pages(`"${currentFolderPath}"`) 
  .where(p => p.file.path !== currentFilePath && !p.file.name.startsWith("MOC"))
  .sort(p => p.file.name, 'asc');

const style = dv.el("style", `
.card { background-color: var(--background-secondary); border: 1px solid var(--background-modifier-border); padding: 14px 18px; border-radius: 8px; margin: 0 auto 12px auto; width: 100%; max-width: 700px; }
.card-title { font-weight: 600; font-size: 1.3em; margin-bottom: 6px; text-align: left; }
.card-title a { text-decoration: none !important; color: var(--text-accent) !important; display: inline-block; text-align: left; }
.card-summary { font-size: 0.9em; color: var(--text-muted); text-align: left; }
`);

for (const page of pages) {
  const resumen = page.resumen || "Sin resumen disponible.";
  const card = dv.el("div", "", {cls: "card"});
  const title = dv.el("div", dv.fileLink(page.file.path, false, page.file.name.replace('.md','')), {cls: "card-title"});
  const summary = dv.el("div", resumen, {cls: "card-summary"});
  card.appendChild(title);
  card.appendChild(summary);
  dv.container.appendChild(card);
}
```"""

    footer_parts = [
        "\n\n---",
        "#### _Ver otros conceptos en este capítulo_:",
        dataview_script,
        "---"
    ]
    
    if atomic_note.get('total_notes_in_chapter', 1) > 1:
        footer_parts.append(f"_Volver al [[{chapter_moc_link_target}|{chapter_moc_display_text}]]_")
        
    footer_parts.append(f"_Volver al [[{main_moc_filename}|{main_moc_display_text}]]_")
    
    return "\n".join(footer_parts)

def process_and_write_atomic_notes(chapters: List[Dict], book_title: str, author: str, year: str, book_root: str) -> List[Dict]:
    """
    Processes chapters into atomic notes and writes them to the vault.
    """
    atomic_chapters_data = []
    all_atomic_notes_for_linking = []

    chapter_num_counter = 1
    for chapter in chapters:
        current_chapter_number = chapter_num_counter if chapter.get('kind') == 'chapter' else None
        
        atomic_notes_in_chapter = []
        note_num_counter = 1
        num_sections = len(chapter['sections'])

        for section in chapter['sections']:
            atomic_note_title = section['title']
            atomic_note_content = section['content']

            decimal_number = f"{current_chapter_number}.{note_num_counter}" if current_chapter_number is not None else None

            atomic_note = {
                "chapter_title": chapter['title'],
                "chapter_number": current_chapter_number,
                "note_title": atomic_note_title,
                "note_decimal_number": decimal_number,
                "content": atomic_note_content,
                "author": author,
                "year": year,
                "total_notes_in_chapter": num_sections
            }

            atomic_note['frontmatter'] = generate_frontmatter(atomic_note, book_title, author)
            atomic_notes_in_chapter.append(atomic_note)
            all_atomic_notes_for_linking.append(atomic_note)
            note_num_counter += 1

        atomic_chapters_data.append({
            "chapter_title": chapter['title'],
            "chapter_number": current_chapter_number,
            "atomic_notes": atomic_notes_in_chapter
        })

        if current_chapter_number is not None:
            chapter_num_counter += 1

    # Create a mapping from note title to its wikilink path
    note_path_mapping = {}
    for chapter_data in atomic_chapters_data:
        chapter_title = chapter_data['chapter_title']
        chapter_number = chapter_data.get('chapter_number')
        folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}" if chapter_number is not None else _sanitize_title_for_filename(chapter_title)

        for atomic_note in chapter_data['atomic_notes']:
            note_title = atomic_note['note_title']
            note_decimal_number = atomic_note['note_decimal_number']

            if note_decimal_number:
                note_filename_base = f"{note_decimal_number} - {_sanitize_title_for_filename(note_title)}"
            else:
                note_filename_base = f"{_sanitize_title_for_filename(note_title)}"
            
            # Obsidian can handle links with or without '.md' but omitting it is cleaner
            full_wikilink_path = f"{folder_name}/{note_filename_base}"
            note_path_mapping[note_title] = full_wikilink_path
            
            # Also map aliases
            if 'alias' in atomic_note['frontmatter']:
                for alias in atomic_note['frontmatter']['alias']:
                     if alias.lower() != note_title.lower():
                        note_path_mapping[alias] = full_wikilink_path

    # Perform wikilink replacement and write notes
    for chapter_data in atomic_chapters_data:
        chapter_title = chapter_data['chapter_title']
        chapter_number = chapter_data.get('chapter_number')
        folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}" if chapter_number is not None else _sanitize_title_for_filename(chapter_title)
        chapter_path = os.path.join(book_root, folder_name)
        os.makedirs(chapter_path, exist_ok=True)

        for atomic_note in chapter_data['atomic_notes']:
            atomic_note['footer'] = _generate_navigation_footer(atomic_note, book_title)

            temp_content = atomic_note['content']
            for raw_target_title, wikilink_target in note_path_mapping.items():
                if raw_target_title.lower() == atomic_note['note_title'].lower():
                    continue
                # Use word boundaries to avoid replacing parts of words
                pattern = r'(?<!\[\[)(?<!\[)' + re.escape(raw_target_title) + r'(?!\]|\]\])'
                replacement = f'[[{wikilink_target}|{raw_target_title}]]'
                temp_content = re.sub(pattern, replacement, temp_content, flags=re.IGNORECASE)
            atomic_note['content'] = temp_content
            
            note_decimal_number = atomic_note['note_decimal_number']
            if note_decimal_number:
                note_filename = f"{note_decimal_number} - {_sanitize_title_for_filename(atomic_note['note_title'])}.md"
            else:
                note_filename = f"{_sanitize_title_for_filename(atomic_note['note_title'])}.md"
            file_path = os.path.join(chapter_path, note_filename)

            final_footer = atomic_note['footer'].replace("{{chapter_path_placeholder}}", folder_name)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---")
                yaml.dump(atomic_note['frontmatter'], f, allow_unicode=True, sort_keys=False)
                f.write("---")
                f.write("\n\n")
                f.write(f"# {atomic_note['note_title']}\n\n")
                f.write(atomic_note['content'])
                f.write(final_footer)

    return atomic_chapters_data