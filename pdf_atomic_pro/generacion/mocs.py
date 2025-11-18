import os
from .notas_atomicas import _sanitize_title_for_filename

def write_mocs(book_root: str, book_title: str, chapters: list):
    """
    Writes the MOC files for the book and chapters.
    """
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
    main_moc_chapter_dataviewjs_script_template = """```dataviewjs
const bookRoot = dv.current().file.folder;
const chapterMOCs = dv.pages(`"{{{{bookRoot}}}}"`)
  .where(p => p.file.name.startsWith("MOC - ") && p.file.name.includes("Capítulo"))
  .sort(p => p.file.name, 'asc');

for (const moc of chapterMOCs) {{
  dv.el("h3", dv.fileLink(moc.file.path));
}}
```"""
    main_moc_all_atomic_notes_dataviewjs_script_template = """```dataviewjs
const bookRoot = dv.current().file.folder;
const allAtomicNotes = dv.pages(`"{{{{bookRoot}}}}"`)
  .where(p => !p.file.name.startsWith("MOC"))
  .sort(p => p.file.name, 'asc');

for (const note of allAtomicNotes) {{
  dv.el("li", dv.fileLink(note.file.path));
}}
```"""

    for chapter_data in chapters:
        chapter_title = chapter_data['chapter_title']
        chapter_kind = chapter_data['chapter_kind']
        chapter_number = chapter_data['chapter_number']

        if chapter_kind == 'chapter' and chapter_number is not None:
            folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}"
        else:
            folder_name = _sanitize_title_for_filename(chapter_title)

        chapter_path = os.path.join(book_root, folder_name)

        # Write Chapter MOC file
        chapter_moc_filename = f"MOC - {_sanitize_title_for_filename(chapter_title)}.md"
        chapter_moc_path = os.path.join(chapter_path, chapter_moc_filename)
        chapter_moc_content = f"# MOC - {chapter_title}\n\n"
        chapter_moc_content += chapter_moc_dataviewjs_script_template
        with open(chapter_moc_path, 'w', encoding='utf-8') as f:
            f.write(chapter_moc_content)

    # Create the main MOC file for the book
    main_moc_filename = f"MOC - {_sanitize_title_for_filename(book_title)}.md"
    main_moc_path = os.path.join(book_root, main_moc_filename)
    with open(main_moc_path, 'w', encoding='utf-8') as f:
        f.write(f"# Mapa de Contenido – {book_title}\n\n")
        f.write("## Capítulos y Secciones Especiales\n")
        f.write(main_moc_chapter_dataviewjs_script_template + "\n\n")
        f.write("## Índice Completo de Notas Atómicas\n")
        f.write(main_moc_all_atomic_notes_dataviewjs_script_template)
