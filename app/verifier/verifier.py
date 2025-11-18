import os
import re
from pathlib import Path
from typing import List, Dict

def verify_links(book_root: Path) -> List[Dict]:
    """
    Audits all wikilinks in the generated Obsidian vault to ensure they point to existing files.
    Returns a list of broken links.
    """
    print(f"  Performing link integrity verification in '{book_root}'...")
    broken_links = []
    
    # Collect all actual file paths in the vault, relative to book_root, in a normalized format
    # Store both the full relative path and the filename without extension for easier lookup
    all_existing_files = set()
    all_existing_filenames_without_ext = set()
    for p in book_root.rglob("*.md"):
        relative_path = str(p.relative_to(book_root)).replace('\\', '/')
        all_existing_files.add(relative_path.lower())
        all_existing_filenames_without_ext.add(p.stem.lower()) # p.stem gives filename without extension
    
    for md_file_path in book_root.rglob("*.md"):
        source_file_relative_path = str(md_file_path.relative_to(book_root)).replace('\\', '/')
        
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all wikilinks
        wikilink_pattern = re.compile(r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]')
        
        for match in wikilink_pattern.finditer(content):
            link_target_raw = match.group(1).strip()
            
            print(f"DEBUG: Source: '{source_file_relative_path}', Raw Link Target: '{link_target_raw}'")

            # Remove heading part if present (e.g., "file#heading" -> "file")
            link_target_file_part = link_target_raw.split('#')[0]
            
            # Obsidian resolves links relative to the current file.
            # We need to simulate this resolution.
            
            # 1. Try to resolve as an absolute path from vault root
            #    (e.g., [[Folder/Subfolder/Note.md]] or [[Folder/Subfolder/Note]])
            resolved_path_from_root_md = f"{link_target_file_part}.md"
            resolved_path_from_root_no_md = link_target_file_part
            
            # 2. Try to resolve as a relative path from the current file's directory
            source_dir = md_file_path.parent
            resolved_relative_path_md = str(source_dir.joinpath(link_target_file_part).relative_to(book_root)).replace('\\', '/') + ".md"
            resolved_relative_path_no_md = str(source_dir.joinpath(link_target_file_part).relative_to(book_root)).replace('\\', '/')
            
            found = False
            
            # Check against full paths (case-insensitive)
            if resolved_path_from_root_md.lower() in all_existing_files or \
               resolved_path_from_root_no_md.lower() in all_existing_files or \
               resolved_relative_path_md.lower() in all_existing_files or \
               resolved_relative_path_no_md.lower() in all_existing_files:
                found = True
            
            # Also check if the link target (without path) matches any existing filename (without extension)
            # This handles cases like [[My Note]] where "My Note.md" exists anywhere
            if not found and link_target_file_part.lower() in all_existing_filenames_without_ext:
                found = True

            print(f"DEBUG:   Resolved paths (from root): '{resolved_path_from_root_md}', '{resolved_path_from_root_no_md}'")
            print(f"DEBUG:   Resolved paths (relative): '{resolved_relative_path_md}', '{resolved_relative_path_no_md}'")
            print(f"DEBUG:   Found: {found}")

            if not found:
                broken_links.append({
                    "source_file": source_file_relative_path,
                    "broken_link": link_target_raw
                })
                
    if broken_links:
        print(f"  Found {len(broken_links)} broken links.")
    else:
        print("  No broken links found.")
        
    return broken_links
