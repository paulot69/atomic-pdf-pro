import re

def _sanitize_title_for_filename(title: str, max_length: int = 50) -> str:
    """
    Sanitizes a title to be used in a filename, removing invalid characters,
    replacing spaces with hyphens, and limiting the length.
    """
    if not title:
        return "sin-titulo"
    # Remove invalid characters for filenames
    title = re.sub(r'[\\/*?:\"<>|«»()[\]{{}}.,;!@#$%^&+=~`]', '', title)
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

def get_main_moc_name(book_title: str, author: str, year: int, config: dict) -> tuple[str, str]:
    """
    Generates the filename and display name for the main book MOC, using configuration rules.
    """
    sanitized_title = _sanitize_title_for_filename(book_title)
    sanitized_author = _sanitize_title_for_filename(author)
    
    # Get naming rule from config
    book_moc_name_format = config['structure']['book_moc_name']
    
    # Format the filename using sanitized titles and year
    # Assuming config format string might use {title}, {author}, {year}
    file_name = book_moc_name_format.format(
        title=sanitized_title,
        author=sanitized_author,
        year=year
    )
    
    # Derive display name from file_name by removing .md extension
    display_name = file_name.replace('.md', '')

    return file_name, display_name
