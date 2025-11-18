import os # Added this line
import re
import yaml
from typing import List, Dict

def _sanitize_title_for_filename(title: str, max_length: int = 100) -> str:
    """
    Sanitizes a title to be used in a filename, removing invalid characters,
    replacing spaces with hyphens, and limiting the length.
    """
    # Remove invalid characters for filenames
    title = re.sub(r'[\\/*?:"<>|«»()\[\]{}.,;!@#$%^&+=~`]', '', title)
    # Replace multiple spaces with a single space, then replace spaces with hyphens
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace(' ', '-')
    # Remove any leading/trailing hyphens
    title = title.strip('-')
    # Limit length
    if len(title) > max_length:
        title = title[:max_length].rsplit('-', 1)[0] # Try to cut at a hyphen
        if not title: # If cutting at hyphen resulted in empty string, just truncate
            title = title[:max_length]
    return title

def _generate_frontmatter(atomic_note: Dict, book_title: str, author: str) -> Dict:
    """Generates the YAML frontmatter for an atomic note."""
    frontmatter = {
        "tags": [
            "status/desarrollo",
            "archivo",
            "tipo/referencia",
            f"fuente/{author.lower().replace(' ', '-')}" # Simplified author tag
        ],
        "resumen": "", # Placeholder as per rule
        "alias": [atomic_note['note_title']]
    }

    # Infer [dominio]/[sub-dominio] tag
    domain = _sanitize_title_for_filename(atomic_note['chapter_title']).lower().replace(' ', '-')
    sub_domain = _sanitize_title_for_filename(atomic_note['note_title']).lower().replace(' ', '-')
    if domain and sub_domain:
        frontmatter['tags'].append(f"{domain}/{sub_domain}")
    elif domain:
        frontmatter['tags'].append(domain)

    return frontmatter

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

# Define a threshold for what constitutes a "long" note for further splitting
MIN_WORDS_FOR_SPLIT = 300
MIN_PARAGRAPHS_FOR_SPLIT = 3

def _split_long_note_into_atomic_notes(long_atomic_note: Dict, book_title: str, author: str, year: int) -> List[Dict]:
    """
    Splits a single long atomic note into multiple smaller atomic notes based on paragraphs.
    """
    new_atomic_notes = []
    content = long_atomic_note['content']
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    if len(paragraphs) < MIN_PARAGRAPHS_FOR_SPLIT and len(content.split()) < MIN_WORDS_FOR_SPLIT:
        # If not long enough, return the original note
        return [long_atomic_note]

    paragraph_counter = 1
    for paragraph in paragraphs:
        if not paragraph:
            continue

        # Generate a simple title for the new atomic note
        # Take the first few words of the paragraph
        paragraph_title = " ".join(paragraph.split()[:8]) + "..." if len(paragraph.split()) > 8 else paragraph
        
        # Create a new atomic note dictionary
        new_note = long_atomic_note.copy() # Copy existing metadata
        new_note['note_title'] = f"{long_atomic_note['note_title']} - Concepto {paragraph_counter}"
        new_note['content'] = paragraph
        new_note['note_decimal_number'] = f"{long_atomic_note['note_decimal_number']}.{paragraph_counter}" if long_atomic_note['note_decimal_number'] else f"Concepto {paragraph_counter}"
        
        # Regenerate frontmatter and footer for the new note
        new_note['frontmatter'] = _generate_frontmatter(new_note, book_title, author)
        new_note['footer'] = _generate_navigation_footer(new_note, book_title)
        
        new_atomic_notes.append(new_note)
        paragraph_counter += 1
    
    return new_atomic_notes

def process_to_atomic_vault(chapters: List[Dict], book_title: str, author: str, year: int) -> List[Dict]:

    """

    Processes the cleaned chapters into an atomic vault structure.

    This involves atomic distillation, metadata enrichment, and navigation implementation.

    """

    print("  Performing atomic distillation and structuring...")

    atomic_chapters_data = []

    all_atomic_notes = [] # To collect all atomic notes for wikilink generation later



    chapter_num_counter = 1

    for chapter in chapters:

        if chapter.get('kind') == 'chapter':

            current_chapter_number = chapter_num_counter

            chapter_num_counter += 1

        else: # special section, no chapter number

            current_chapter_number = None



        atomic_notes_in_chapter = []

        note_num_counter = 1

        for section in chapter['sections']:

            atomic_note_title = section['title']

            atomic_note_content = section['content']



            # Fase 1: Destilación Atómica (simplificada: cada sección es una nota atómica)

            # Assign decimal number

            if current_chapter_number is not None:

                decimal_number = f"{current_chapter_number}.{note_num_counter}"

            else:

                decimal_number = None # Special sections don't get a decimal number



            atomic_note = {

                "chapter_title": chapter['title'],

                "chapter_number": current_chapter_number,

                "chapter_kind": chapter['kind'],

                "note_title": atomic_note_title,

                "note_decimal_number": decimal_number,

                "content": atomic_note_content,

                "frontmatter": {},

                "footer": ""       # Will be populated in Fase 3

            }

            

            # Fase 2: Enriquecimiento de Metadatos (YAML)

            atomic_note['frontmatter'] = _generate_frontmatter(atomic_note, book_title, author)

            

            # Fase 3: Implementación de Navegación (Pie de Página)

            atomic_note['footer'] = _generate_navigation_footer(atomic_note, book_title)

            

            # Check if this is a "long note" that needs further splitting

            # This typically happens if split_chapter_into_sections returned only one section

            # and that section is long.

            if len(chapter['sections']) == 1 and len(atomic_note['content'].split()) > MIN_WORDS_FOR_SPLIT:

                print(f"  Splitting long note: '{atomic_note['note_title']}' into smaller atomic notes...")

                split_notes = _split_long_note_into_atomic_notes(atomic_note, book_title, author, year)

                atomic_notes_in_chapter.extend(split_notes)

                all_atomic_notes.extend(split_notes)

                # The original long note is effectively replaced by its split parts

            else:

                atomic_notes_in_chapter.append(atomic_note)

                all_atomic_notes.append(atomic_note)

            

                        

            

                                        atomic_notes_in_chapter.append(atomic_note)

            

                        

            

                                        all_atomic_notes.append(atomic_note)

            

                        

            

                                    note_num_counter += 1

            

                        

            

                                    

            

            

            

                        

            

            

            

                    

            

            

            

                    atomic_chapters_data.append({

            

            

            

                        "chapter_title": chapter['title'],

            

            

            

                        "chapter_number": current_chapter_number,

            

            

            

                        "chapter_kind": chapter['kind'],

            

            

            

                        "atomic_notes": atomic_notes_in_chapter

            

            

            

                    })

            

            

            

                print("  Performing wikilink generation...")

            

                # Create a comprehensive mapping from raw note title to its full sanitized path for wikilinking

            

                # This mapping is built *after* all atomic notes (including split ones) have been generated.

            

                note_path_mapping = {}

            

                for chapter_data in atomic_chapters_data:

            

                    chapter_title = chapter_data['chapter_title']

            

                    chapter_kind = chapter_data['chapter_kind']

            

                    chapter_number = chapter_data['chapter_number']

            

            

            

                    # Chapter Folder Naming (must match writer.py)

            

                    if chapter_kind == 'chapter' and chapter_number is not None:

            

                        folder_name = f"Capítulo-{chapter_number:02d}---{_sanitize_title_for_filename(chapter_title)}"

            

                    else: # special section

            

                        folder_name = _sanitize_title_for_filename(chapter_title)

            

            

            

                    for atomic_note in chapter_data['atomic_notes']:

            

                        note_title = atomic_note['note_title']

            

                        note_decimal_number = atomic_note['note_decimal_number']

            

                        

            

                        if note_decimal_number:

            

                            note_filename = f"{note_decimal_number}---{_sanitize_title_for_filename(note_title)}.md"

            

                        else:

            

                            note_filename = f"Nota---{_sanitize_title_for_filename(note_title)}.md"

            

                        

            

                        full_relative_path = os.path.join(folder_name, note_filename).replace('\\', '/')

            

                        note_path_mapping[note_title] = full_relative_path

            

                        # Also add aliases if they exist in frontmatter

            

                        if 'alias' in atomic_note['frontmatter']:

            

                            for alias in atomic_note['frontmatter']['alias']:

            

                                note_path_mapping[alias] = full_relative_path

            

            

            

                # Perform wikilink replacement using the comprehensive mapping

            

                for note in all_atomic_notes:

            

                    for raw_target_title, sanitized_target_path in note_path_mapping.items():

            

                        # Ensure we don't link to ourselves

            

                        if raw_target_title == note['note_title']:

            

                            continue

            

            

            

                        # Create a more flexible regex pattern for matching the raw_target_title

            

                        # - re.escape to handle special characters in the title

            

                        # - Use non-word boundaries or lookarounds to match phrases, not just single words

            

                        # - re.IGNORECASE for case-insensitive matching

            

                        # - Lookbehind (?<!\[\[) and lookahead (?!\]\]) to avoid replacing already existing wikilinks

            

                        

            

                        # This pattern will match the raw_target_title as a standalone phrase,

            

                        # allowing for punctuation immediately before or after it, and case-insensitivity.

            

                        # It avoids replacing parts of other words or already existing wikilinks.

            

                        

            

                        # The `\b` word boundary is problematic for multi-word titles.

            

                        # Let's try to match the phrase, and ensure it's surrounded by non-word characters or start/end of string.

            

                        

            

                        # Pattern:

            

                        # (?<!\[\[) : Not preceded by [[

            

                        # (?:^|(?<=\W)) : Preceded by start of string or a non-word character

            

                        # (re.escape(raw_target_title)) : The actual title, escaped

            

                        # (?:$|(?=\W)) : Followed by end of string or a non-word character

            

                        # (?!\]\]) : Not followed by ]]

            

                        

            

                        # This pattern is more robust for multi-word titles and punctuation.

            

                        # It will match "Equipo de aventureros" in "Aquí está Equipo de aventureros."

            

                        # but not in "Equipo de aventureros_extra".

            

                        

            

                        pattern = r'(?<!\[\[)(?:^|(?<=\W))(' + re.escape(raw_target_title) + r')(?:$|(?=\W))(?!\]\])'

            

                        

            

                        # Use re.IGNORECASE for case-insensitive matching

            

                        note['content'] = re.sub(pattern, rf'[[{sanitized_target_path}|\1]]', note['content'], flags=re.IGNORECASE)

            

                print("  Wikilink generation complete.")

            

            

            

                print("  Atomic distillation and metadata enrichment complete.")

    return atomic_chapters_data
