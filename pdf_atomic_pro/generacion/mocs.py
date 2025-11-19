import os
import yaml
from pathlib import Path
from .utils import _sanitize_title_for_filename, get_main_moc_name

def _write_metadata_file(book_root: str, book_title: str, author: str, year: str):
    """
    Gathers all unique tags by scanning the generated Markdown files
    and writes them to a dedicated metadata file for auditing.
    """
    print("Generating metadata file with all tags...")
    all_tags = set()
    book_root_path = Path(book_root)

    # Iterate over all generated markdown files
    for md_file in book_root_path.rglob("*.md"):
        # Exclude MOCs and the metadata file itself to avoid recursion
        if md_file.name.startswith("MOC") or "METADATA" in str(md_file):
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find the YAML frontmatter block
                if content.startswith("---"):
                    yaml_content = content.split("---")[1]
                    frontmatter = yaml.safe_load(yaml_content)
                    if isinstance(frontmatter, dict) and 'tags' in frontmatter:
                        all_tags.update(frontmatter['tags'])
        except Exception as e:
            print(f"Warning: Could not process file {md_file} for tag extraction: {e}")


    if not all_tags:
        print("No tags found to generate metadata file.")
        return

    sanitized_book_title = _sanitize_title_for_filename(book_title)
    metadata_folder_name = f"METADATA - {sanitized_book_title}"
    metadata_folder_path = os.path.join(book_root, metadata_folder_name)
    os.makedirs(metadata_folder_path, exist_ok=True)
    
    tags_note_path = os.path.join(metadata_folder_path, f"Tags - {sanitized_book_title}.md")
    
    sorted_tags = sorted(list(all_tags))
    
    content = f"# Tags para '{book_title}'\n\n"
    content += "Lista de todos los tags únicos utilizados en este libro, en orden alfabético.\n\n"
    content += "\n".join(f"- `{tag}`" for tag in sorted_tags)
    
    with open(tags_note_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated tag metadata file: {tags_note_path}")

def write_mocs(book_root: str, book_title: str, author: str, year: str, chapters: list):
    """
    Writes the MOC files for the book and chapters, applying conditional and naming rules.
    """
    # --- DataviewJS Templates (un-indented and syntactically correct) ---
    chapter_moc_script = """```dataviewjs
const currentFolderPath = dv.current().file.folder;
const pages = dv.pages(`"${currentFolderPath}"`) 
  .where(p => !p.file.name.startsWith("MOC"))
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
  const title = dv.el("div", dv.fileLink(page.file.path, false, page.file.name.replace('.md','') ), {cls: "card-title"});
  const summary = dv.el("div", resumen, {cls: "card-summary"});
  card.appendChild(title);
  card.appendChild(summary);
  dv.container.appendChild(card);
}
```"""

    main_moc_chapters_script = """```dataviewjs
const bookRoot = dv.current().file.folder;
const chapterMOCs = dv.pages(`"${bookRoot}"`) 
  .where(p => p.file.name.startsWith("MOC -") && p.file.folder.contains(bookRoot))
  .sort(p => p.file.name, 'asc');
for (const moc of chapterMOCs) {
  dv.el("h3", dv.fileLink(moc.file.path));
}
```"""

    main_moc_all_notes_script = """```dataviewjs
const bookRoot = dv.current().file.folder;
const allAtomicNotes = dv.pages(`"${bookRoot}"`) 
  .where(p => !p.file.name.startsWith("MOC") && !p.file.folder.includes("METADATA"))
  .sort(p => p.file.name, 'asc');
dv.list(allAtomicNotes.map(p => dv.fileLink(p.file.path)));
```"""

    # --- Rule 1: Write Chapter MOCs (conditionally) ---
    print("Writing MOC files...")
    for chapter_data in chapters:
        # NOTE: The creation of chapter directories is now handled in 'notas_atomicas.py'
        # We only write the MOC if needed.
        if len(chapter_data.get('atomic_notes', [])) > 1:
            chapter_title = chapter_data['chapter_title']
            chapter_number = chapter_data.get('chapter_number')

            if chapter_number is not None:
                folder_name = f"Capítulo {chapter_number:02d} - {_sanitize_title_for_filename(chapter_title)}"
            else:
                folder_name = _sanitize_title_for_filename(chapter_title)
            
            # The folder is now expected to exist.
            chapter_path = os.path.join(book_root, folder_name)

            moc_filename = f"MOC - {_sanitize_title_for_filename(chapter_title)}.md"
            moc_path = os.path.join(chapter_path, moc_filename)
            moc_content = f"# MOC - {chapter_title}\n\n{chapter_moc_script}"
            
            with open(moc_path, 'w', encoding='utf-8') as f:
                f.write(moc_content)
            print(f"Generated conditional MOC for chapter: {chapter_title}")

    # --- Rule 2: Write Main MOC (new naming convention) ---
    main_moc_filename, _ = get_main_moc_name(book_title, author, year)
    main_moc_path = os.path.join(book_root, main_moc_filename)
    
    with open(main_moc_path, 'w', encoding='utf-8') as f:
        f.write(f"# Mapa de Contenido – {book_title}\n\n")
        f.write("## Capítulos\n")
        f.write(main_moc_chapters_script + "\n\n")
        f.write("## Todas las Notas\n")
        f.write(main_moc_all_notes_script)
    print(f"Generated main MOC: {main_moc_path}")

    # --- Rule 3: Write Metadata File ---
    _write_metadata_file(book_root, book_title, author, year)
