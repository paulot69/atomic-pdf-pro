import os
import yaml
import traceback
import re

def _clean_title_for_filename(title):
    """Sanitizes a title to be used in a folder or file name."""
    # Remove chapter/section prefixes
    title = re.sub(r'^\s*(Cap[ií]tulo|Chapter|CAP[IÍ]TULO|CHAPTER|Cap\.?)\s*([IVXLCDM\d]+)\.?:?\s*', '', title, flags=re.IGNORECASE)
    # Remove special characters not suitable for filenames
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    return title.strip()

def write_vault(output_path, book_title, author, year, chapters):
    """
    Writes the processed chapters to the specified output directory, creating the full
    Obsidian vault structure.
    """
    try:
        book_root = os.path.join(output_path, book_title)
        os.makedirs(book_root, exist_ok=True)

        for chapter in chapters:
            chapter_title = chapter["title"]
            clean_title = _clean_title_for_filename(chapter_title)

            if chapter["type"] == "chapter":
                folder_name = f"Capítulo {chapter['number']:02d} - {clean_title}"
            else: # section
                folder_name = chapter_title

            chapter_path = os.path.join(book_root, folder_name)
            os.makedirs(chapter_path, exist_ok=True)

            note_filename = f"Nota - {clean_title}.md"
            file_path = os.path.join(chapter_path, note_filename)

            frontmatter = {
                "titulo_libro": book_title,
                "autor": author,
                "ano": year,
                "tipo": chapter["type"],
                "numero_capitulo": chapter.get("number"),
                "titulo_capitulo": chapter_title,
            }
            # Remove chapter number if it's a section
            if chapter["type"] == "section":
                del frontmatter["numero_capitulo"]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True, sort_keys=False)
                f.write("---\n\n")
                f.write(f"# {chapter_title}\n\n")
                f.write(chapter["content"])

        # Create the main MOC file
        moc_file_path = os.path.join(book_root, f"MOC - {book_title}.md")
        with open(moc_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Índice – {book_title}\n\n")

            sections = [c for c in chapters if c["type"] == "section"]
            if sections:
                f.write("## Secciones\n")
                for s in sections:
                    clean_title = _clean_title_for_filename(s['title'])
                    f.write(f"- [[{s['title']}/Nota - {clean_title}]]\n")
                f.write("\n")

            regular_chapters = [c for c in chapters if c["type"] == "chapter"]
            if regular_chapters:
                f.write("## Capítulos\n")
                for c in regular_chapters:
                    clean_title = _clean_title_for_filename(c['title'])
                    folder_name = f"Capítulo {c['number']:02d} - {clean_title}"
                    f.write(f"- [[{folder_name}/Nota - {clean_title}]]\n")

        print(f"Successfully created vault at: {book_root}")

    except Exception as e:
        print(f"An error occurred during file writing: {e}")
        traceback.print_exc()
