import os
import re
import logging # NEW: Import logging
from typing import List, Dict, Optional
from jinja2 import Template
from pathlib import Path

from .utils import _sanitize_title_for_filename, get_main_moc_name
from .summarizer import generate_fallback_summary

def _get_author_lastname(author: str) -> str:
    """Extracts a simplified last name from the author's full name."""
    if not author:
        return "unknown"
    # Simple split, takes the last word, sanitizes, and lowercases.
    lastname = author.split(' ')[-1]
    return re.sub(r'[^a-z0-9]', '', lastname.lower())

def _infer_domain_tag(chapter_title: str, semantic_tags: List[str]) -> str:
    """
    A simple heuristic to infer a domain tag.
    It should be improved with a more sophisticated engine, maybe checking against a known tag list.
    """
    # For now, return a default placeholder.
    return "domain/por-clasificar"

def process_and_write_atomic_notes(chapters: List[Dict], book_title: str, author: str, year: str, book_root: str, config: Dict, use_ai: bool = True, generate_summaries: bool = True) -> List[Dict]:
    """
    Processes chapters into atomic notes using a template-based approach and writes them to the vault.
    """
    # 1. Use passed configuration and templates
    try:
        # Resolve template path relative to the project root, using the passed config
        # Assuming run from root, templates path in config is relative to root.
        # But if we rely on relative paths, we must be careful.
        # The safest bet is to resolve relative to CWD (root) OR resolve relative to this file's package root if intended.
        # Given config now says 'pdf_atomic_pro/config/templates/...', resolving from CWD (Repo Root) is correct.

        project_root = Path.cwd()
        template_path = project_root / config['templates']['atomic_note']
        
        if not template_path.exists():
             # Fallback: try resolving relative to file location if CWD fails?
             # Or maybe project_root was intended to be the package root?
             # Let's try locating it relative to this file's parent's parent's parent (pdf_atomic_pro root)
             # this file is in pdf_atomic_pro/core/generacion/
             # parents[0] = generacion, parents[1] = core, parents[2] = pdf_atomic_pro
             package_root = Path(__file__).resolve().parents[2]
             # But config string includes 'pdf_atomic_pro/', so it expects repo root.
             # If we are running from repo root, CWD is fine.
             pass

        with open(template_path, 'r', encoding='utf-8') as f:
            note_template = Template(f.read())
    except (FileNotFoundError, ValueError, KeyError) as e:
        raise RuntimeError(f"Failed to load or parse configuration/templates at {template_path if 'template_path' in locals() else 'unknown'}: {e}")

    atomic_chapters_data = []
    all_atomic_notes_for_linking = []

    metadata_engine = None
    if use_ai:
        try:
             # Lazy import to avoid hard dependency on AI libs if not used
             from pdf_atomic_pro.core.ai_connector import MetadataEngine
             metadata_engine = MetadataEngine()
        except ImportError:
             logging.warning("MetadataEngine could not be imported. AI features disabled.")
             metadata_engine = None

    # 2. First pass: Prepare all note data without writing
    chapter_num_counter = 1
    for chapter in chapters:
        current_chapter_number = chapter_num_counter if chapter.get('kind') == 'chapter' else None
        atomic_notes_in_chapter = []
        note_num_counter = 1

        for section in chapter['sections']:
            summary = ""
            semantic_tags = []
            cleaned_content = re.sub(r'\s+', ' ', section['content'].strip())

            if use_ai and metadata_engine and cleaned_content:
                try:
                    ai_metadata = metadata_engine.get_metadata(cleaned_content)
                    if generate_summaries:
                        summary = ai_metadata.get('summary', '')
                    semantic_tags = ai_metadata.get('tags', [])
                except Exception as e:
                    print(f"Warning: AI failed for note '{section['title']}', using fallback. Error: {e}")
            
            if generate_summaries and not summary:
                summary = generate_fallback_summary(section['content'])
            
            decimal_number = f"{current_chapter_number}.{note_num_counter}" if current_chapter_number is not None else None

            atomic_note = {
                "chapter_title": chapter['title'],
                "chapter_number": current_chapter_number,
                "note_title": section['title'],
                "note_decimal_number": decimal_number,
                "content": section['content'],
                "author": author,
                "year": year,
                "summary": summary,
                "semantic_tags": semantic_tags,
                "level": chapter.get('level', 1)
            }
            atomic_notes_in_chapter.append(atomic_note)
            all_atomic_notes_for_linking.append(atomic_note)
            note_num_counter += 1
        
        atomic_chapters_data.append({
            "chapter_title": chapter['title'],
            "chapter_number": current_chapter_number,
            "level": chapter.get('level', 1),
            "atomic_notes": atomic_notes_in_chapter
        })

        if current_chapter_number is not None:
            chapter_num_counter += 1

    # 3. Create a mapping from note title to its future wikilink path
    note_path_mapping = {}
    structure_rules = config['structure']
    for chapter_data in atomic_chapters_data:
        chapter_title_sanitized = _sanitize_title_for_filename(chapter_data['chapter_title'])
        chapter_number = chapter_data.get('chapter_number')
        
        folder_name_format = structure_rules['chapter_folder_name']
        folder_name = folder_name_format.format(chapter_number=chapter_number, chapter_title=chapter_title_sanitized) if chapter_number is not None else chapter_title_sanitized

        for note in chapter_data['atomic_notes']:
            note_title_sanitized = _sanitize_title_for_filename(note['note_title'])
            note_filename_format = structure_rules['atomic_note_name']
            note_filename_base = note_filename_format.format(
                chapter_number=chapter_number, 
                note_number=note['note_decimal_number'].split('.')[-1] if note.get('note_decimal_number') else 'X',
                note_title=note_title_sanitized
            )
            full_wikilink_path = f"{folder_name}/{note_filename_base}"
            note_path_mapping[note['note_title']] = full_wikilink_path

    # 4. Perform wikilinking, render templates, and write notes
    path_stack = [book_root]
    main_moc_filename, _ = get_main_moc_name(book_title, author, year, config) # NEW: Pass config

    for chapter_data in atomic_chapters_data:
        chapter_title_sanitized = _sanitize_title_for_filename(chapter_data['chapter_title'])
        chapter_number = chapter_data.get('chapter_number')
        chapter_level = chapter_data.get('level', 1)

        folder_name_format = structure_rules['chapter_folder_name']
        folder_name = folder_name_format.format(chapter_number=chapter_number, chapter_title=chapter_title_sanitized) if chapter_number is not None else chapter_title_sanitized
        
        chapter_moc_name_format = structure_rules['chapter_moc_name']
        chapter_moc_filename = chapter_moc_name_format.format(chapter_number=chapter_number, chapter_title=chapter_title_sanitized) if chapter_number is not None else f"MOC - {chapter_title_sanitized}.md"

        parent_path = path_stack[chapter_level - 1]
        chapter_path = os.path.join(parent_path, folder_name)
        os.makedirs(chapter_path, exist_ok=True)

        if len(path_stack) > chapter_level:
            path_stack[chapter_level] = chapter_path
            path_stack = path_stack[:chapter_level + 1]
        else:
            path_stack.append(chapter_path)

        for note in chapter_data['atomic_notes']:
            temp_content = note['content']
            for raw_target_title, wikilink_target in note_path_mapping.items():
                if raw_target_title.lower() == note['note_title'].lower():
                    continue
                pattern = r'\b' + re.escape(raw_target_title) + r'\b'
                replacement = f'[[{wikilink_target}|{raw_target_title}]]'
                temp_content = re.sub(pattern, replacement, temp_content, flags=re.IGNORECASE)
            
            template_context = {
                'author_lastname': _get_author_lastname(author),
                'domain_tag_placeholder': _infer_domain_tag(chapter_data['chapter_title'], note['semantic_tags']),
                'all_domain_tags': note['semantic_tags'],
                'note_title': note['note_title'],
                'note_content': temp_content,
                'summary': note['summary'],
                'chapter_moc_filename': f"{folder_name}/{chapter_moc_filename}",
                'book_moc_filename': main_moc_filename
            }

            rendered_content = note_template.render(template_context)
            
            note_title_sanitized = _sanitize_title_for_filename(note['note_title'])
            note_filename_format = structure_rules['atomic_note_name']
            note_filename_base = note_filename_format.format(
                chapter_number=chapter_number, 
                note_number=note['note_decimal_number'].split('.')[-1] if note.get('note_decimal_number') else 'X',
                note_title=note_title_sanitized
            )
            file_path = os.path.join(chapter_path, f"{note_filename_base}.md")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content) # Corrected typo

    return atomic_chapters_data