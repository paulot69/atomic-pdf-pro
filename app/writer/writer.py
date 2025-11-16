import os
import yaml
import traceback

def write_vault(output_path, book_title, author, year, chapters):
    """
    Writes the processed chapters to the specified output directory, creating the full
    Obsidian vault structure.
    """
    try:
        # 1. Create the root directory for the book
        book_root = os.path.join(output_path, book_title)
        os.makedirs(book_root, exist_ok=True)

        # 2. Create chapter files
        for chapter in chapters:
            chapter_number = chapter["number"]

            # Create chapter directory (e.g., /Capítulo 01/)
            chapter_dir_name = f"Capítulo {chapter_number:02d}"
            chapter_path = os.path.join(book_root, chapter_dir_name)
            os.makedirs(chapter_path, exist_ok=True)

            # Create chapter markdown file (e.g., /Capítulo 01/01 - Capítulo 01.md)
            file_name = f"{chapter_number:02d} - {chapter_dir_name}.md"
            file_path = os.path.join(chapter_path, file_name)

            # Create YAML frontmatter
            frontmatter = {
                "titulo": f"Capítulo {chapter_number:02d}",
                "libro": book_title,
                "autor": author,
                "año": year,
                "tipo": "capitulo",
                "capitulo": chapter_number,
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, allow_unicode=True)
                f.write("---\n\n")
                f.write(f"# Capítulo {chapter_number:02d}\n\n")
                f.write(chapter["content"])

        # 3. Create the main MOC file
        moc_file_path = os.path.join(book_root, f"_MOC - {book_title}.md")
        with open(moc_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Mapa del Libro – {book_title}\n\n")
            f.write("## Capítulos\n\n")
            for chapter in chapters:
                chapter_number = chapter["number"]
                dir_name = f"Capítulo {chapter_number:02d}"
                file_base = f"{chapter_number:02d} - {dir_name}"
                f.write(f"- [[{dir_name}/{file_base}]]\n")

        # 4. Create the metadata.yaml file
        metadata = {
            "titulo": book_title,
            "autor": author,
            "año": year,
            "capitulos": len(chapters)
        }
        metadata_file_path = os.path.join(book_root, "metadata.yaml")
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)

        print(f"Successfully created vault at: {book_root}")

    except Exception as e:
        print(f"An error occurred during file writing: {e}")
        traceback.print_exc()
