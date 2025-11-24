import os
import yaml
from pathlib import Path
from typing import Dict # NEW: Import Dict
from .utils import _sanitize_title_for_filename, get_main_moc_name
from jinja2 import Template

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

def write_mocs(book_root: str, book_title: str, author: str, year: str, chapters: list, config: Dict):
    """
    Writes the MOC files for the book and chapters using a template-based approach.
    """
    # 1. Use passed configuration and templates
    try:
        structure_rules = config['structure']
        project_root = Path(__file__).resolve().parents[3]
        
        chapter_template_path = project_root / config['templates']['chapter_moc']
        book_template_path = project_root / config['templates']['book_moc']

        with open(chapter_template_path, 'r', encoding='utf-8') as f:
            chapter_moc_template = Template(f.read())
        with open(book_template_path, 'r', encoding='utf-8') as f:
            book_moc_template = Template(f.read())
            
    except (FileNotFoundError, ValueError, KeyError) as e:
        raise RuntimeError(f"Failed to load or parse MOC configuration/templates: {e}")

    print("Writing MOC files...")
    main_moc_filename, _ = get_main_moc_name(book_title, author, year, config) # NEW: Pass config

    # 2. Write Chapter MOCs
    for chapter_data in chapters:
        # A MOC is only needed if there is more than one note in the chapter.
        if len(chapter_data.get('atomic_notes', [])) > 1:
            chapter_title = chapter_data['chapter_title']
            chapter_number = chapter_data.get('chapter_number')
            chapter_title_sanitized = _sanitize_title_for_filename(chapter_title)

            folder_name_format = structure_rules['chapter_folder_name']
            folder_name = folder_name_format.format(chapter_number=chapter_number, chapter_title=chapter_title_sanitized) if chapter_number is not None else chapter_title_sanitized
            
            chapter_path = os.path.join(book_root, folder_name)
            
            moc_name_format = structure_rules['chapter_moc_name']
            moc_filename = moc_name_format.format(chapter_number=chapter_number, chapter_title=chapter_title_sanitized) if chapter_number is not None else f"MOC - {chapter_title_sanitized}.md"
            moc_path = os.path.join(chapter_path, moc_filename)

            template_context = {
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "book_moc_filename": main_moc_filename
            }
            
            moc_content = chapter_moc_template.render(template_context)
            
            with open(moc_path, 'w', encoding='utf-8') as f:
                f.write(moc_content)
            print(f"Generated MOC for chapter: {chapter_title}")

    # 3. Write Main Book MOC
    main_moc_path = os.path.join(book_root, main_moc_filename)
    book_template_context = {
        "book_title": book_title
    }
    main_moc_content = book_moc_template.render(book_template_context)
    
    with open(main_moc_path, 'w', encoding='utf-8') as f:
        f.write(main_moc_content)
    print(f"Generated main MOC: {main_moc_path}")

    # --- Rule 4: Write Metadata File (unchanged) ---
    _write_metadata_file(book_root, book_title, author, year)
