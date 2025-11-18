import os
import yaml
import traceback
import re
from app.atomic_distiller.distiller import _sanitize_title_for_filename # Import the robust version

def write_vault(output_path: str, book_title: str, author: str, year: int, chapters: list):
    """
    Writes the hierarchical chapter/section structure to the Obsidian vault.
    """
    try:
        # Update book_root to [Año] - [Título del Libro] - [Autor]
        book_root_name = f"{year} - {_sanitize_title_for_filename(book_title)} - {_sanitize_title_for_filename(author)}"
        book_root = os.path.join(output_path, book_root_name)
        os.makedirs(book_root, exist_ok=True)

        # Store paths for MOC generation
        chapter_moc_links = []

        # Define dataviewjs script for chapter MOCs (cards)
        chapter_moc_dataviewjs_script_template = """```dataviewjs
const currentFolderPath = dv.current().file.folder;
const pages = dv.pages(`"{{{{currentFolderPath}}}}"`)
  .where(p => !p.file.name.startsWith("MOC"))
  .sort(p => p.file.name, 'asc');

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
```"""

        # Define dataviewjs script for main MOC (listing chapter MOCs)
        main_moc_chapter_dataviewjs_script_template = """```dataviewjs
const bookRoot = dv.current().file.folder;
const chapterMOCs = dv.pages(`"{{{{bookRoot}}}}"`)
  .where(p => p.file.name.startsWith("MOC - ") && p.file.name.includes("Capítulo"))
  .sort(p => p.file.name, 'asc');

for (const moc of chapterMOCs) {{
  dv.el("h3", dv.fileLink(moc.file.path));
}}
```"""

        # Define dataviewjs script for main MOC (listing all atomic notes)
        main_moc_all_atomic_notes_dataviewjs_script_template = """```dataviewjs
const bookRoot = dv.current().file.folder;
const allAtomicNotes = dv.pages(`"{{{{bookRoot}}}}"`)
  .where(p => !p.file.name.startsWith("MOC"))
  .sort(p => p.file.name, 'asc');

for (const note of allAtomicNotes) {{
  dv.el("li", dv.fileLink(note.file.path));
}}
```"""


        for chapter_data in chapters: # 'chapters' now contains atomic_chapters_data
            chapter_title = chapter_data['chapter_title']
            chapter_kind = chapter_data['chapter_kind']
            chapter_number = chapter_data['chapter_number']

            # Chapter Folder Naming
            if chapter_kind == 'chapter' and chapter_number is not None:
                folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}"
            else: # special section
                folder_name = _sanitize_title_for_filename(chapter_title)

            chapter_path = os.path.join(book_root, folder_name)
            os.makedirs(chapter_path, exist_ok=True)

            # Generate Chapter MOC
            chapter_moc_filename = f"MOC - {_sanitize_title_for_filename(chapter_title)}.md"
            chapter_moc_path = os.path.join(chapter_path, chapter_moc_filename)
            chapter_moc_links.append({
                "title": chapter_title,
                "path": os.path.join(folder_name, chapter_moc_filename),
                "kind": chapter_kind,
                "number": chapter_number
            })

            # Write Atomic Notes
            for atomic_note in chapter_data['atomic_notes']:
                note_title = atomic_note['note_title']
                note_decimal_number = atomic_note['note_decimal_number']
                
                if note_decimal_number:
                    note_filename = f"{note_decimal_number} - {_sanitize_title_for_filename(note_title)}.md"
                else:
                    note_filename = f"Nota - {_sanitize_title_for_filename(note_title)}.md"
                
                file_path = os.path.join(chapter_path, note_filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    # Write YAML Frontmatter
                    f.write("---\n")
                    yaml.dump(atomic_note['frontmatter'], f, allow_unicode=True, sort_keys=False)
                    f.write("---\n\n")
                    
                    # Write Note Content
                    f.write(f"# {note_title}\n\n")
                    f.write(atomic_note['content'])
                    
                    # Write Navigation Footer
                    # Replace placeholder in dataviewjs script with actual chapter path
                    footer_content = atomic_note['footer'].replace("{{chapter_path_placeholder}}", chapter_path.replace(book_root + os.sep, '').replace('\\', '/'))
                    f.write(footer_content)

            # Write Chapter MOC file
            chapter_moc_content = f"# MOC - {chapter_title}\n\n"
            chapter_moc_content += chapter_moc_dataviewjs_script_template
            with open(chapter_moc_path, 'w', encoding='utf-8') as f:
                f.write(chapter_moc_content)

        # Create the main MOC file for the book
        main_moc_filename = f"MOC - {_sanitize_title_for_filename(book_title)}.md"
        main_moc_path = os.path.join(book_root, main_moc_filename)
        with open(main_moc_path, 'w', encoding='utf-8') as f:
            f.write(f"# Mapa de Contenido – {book_title}\n\n")

            # DataviewJS for Chapter MOCs
            f.write("## Capítulos y Secciones Especiales\n")
            f.write(main_moc_chapter_dataviewjs_script_template + "\n\n")

            # DataviewJS for All Atomic Notes
            f.write("## Índice Completo de Notas Atómicas\n")
            f.write(main_moc_all_atomic_notes_dataviewjs_script_template)

    except Exception as e:
        print(f"An error occurred during file writing: {e}")
        traceback.print_exc()
