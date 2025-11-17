import os
import yaml
import traceback
import re

def _sanitize_for_filename(text: str) -> str:
    """Sanitizes a string to be used as a valid file or folder name."""
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = text.replace('\n', ' ').strip()
    return text

def write_vault(output_path: str, book_title: str, author: str, year: int, chapters: list):
    """
    Writes the hierarchical chapter/section structure to the Obsidian vault.
    """
    try:
        book_root = os.path.join(output_path, _sanitize_for_filename(book_title))
        os.makedirs(book_root, exist_ok=True)

        chapter_counter = 1

        for chapter in chapters:
            chapter_title = chapter['title']

            if chapter['kind'] == 'chapter':
                folder_name = f"{chapter_counter:02d} - {_sanitize_for_filename(chapter_title)}"
                chapter_counter += 1
            else: # special section
                folder_name = _sanitize_for_filename(chapter_title)

            chapter_path = os.path.join(book_root, folder_name)
            os.makedirs(chapter_path, exist_ok=True)

            # Create a local MOC for the chapter's sections
            local_moc_content = [f"# {chapter_title}\n"]

            for section in chapter['sections']:
                section_title = section['title']
                note_filename = f"Nota - {_sanitize_for_filename(section_title)}.md"
                file_path = os.path.join(chapter_path, note_filename)

                # Add to local MOC
                local_moc_content.append(f"- [[{note_filename.replace('.md', '')}]]")

                frontmatter = {
                    "titulo_libro": book_title,
                    "autor": author,
                    "ano": year,
                    "tipo": "section",
                    "capitulo_titulo": chapter_title,
                    "capitulo_tipo": chapter['kind'],
                }
                if chapter.get('number') is not None:
                    frontmatter["capitulo_numero"] = chapter['number']

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("---\n")
                    yaml.dump(frontmatter, f, allow_unicode=True, sort_keys=False)
                    f.write("---\n\n")
                    f.write(f"# {section_title}\n\n")
                    f.write(section['content'])

            # Write the local MOC file
            local_moc_path = os.path.join(chapter_path, f"MOC - {_sanitize_for_filename(chapter_title)}.md")
            with open(local_moc_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(local_moc_content))

        # Create the main MOC file for the book
        main_moc_path = os.path.join(book_root, f"MOC - {book_title}.md")
        with open(main_moc_path, 'w', encoding='utf-8') as f:
            f.write(f"# Mapa de Contenido – {book_title}\n\n")

            special_sections = [c for c in chapters if c['kind'] == 'special']
            if special_sections:
                f.write("## Secciones especiales\n")
                for s in special_sections:
                    folder_name = _sanitize_for_filename(s['title'])
                    f.write(f"- [[{folder_name}/MOC - {folder_name}|{s['title']}]]\n")
                f.write("\n")

            regular_chapters = [c for c in chapters if c['kind'] == 'chapter']
            if regular_chapters:
                f.write("## Capítulos\n")
                # Reset counter for display
                chapter_counter = 1
                for c in regular_chapters:
                    folder_name = f"{chapter_counter:02d} - {_sanitize_for_filename(c['title'])}"
                    f.write(f"{c['number']}. [[{folder_name}/MOC - {_sanitize_for_filename(c['title'])}|{c['title']}]]\n")
                    chapter_counter += 1

    except Exception as e:
        print(f"An error occurred during file writing: {e}")
        traceback.print_exc()
