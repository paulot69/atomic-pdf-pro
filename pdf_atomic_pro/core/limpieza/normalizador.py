import re
from typing import List, Dict
from collections import Counter

def normalize_text(structured_lines: List[Dict]) -> str:
    """
    Converts a list of structured text lines into a single string,
    intelligently reconstructing paragraphs based on vertical spacing.
    """
    if not structured_lines:
        return ""

    # Step 1: Reconstruct paragraphs from structured lines
    paragraphs = []
    current_paragraph_lines = []

    for i in range(len(structured_lines)):
        line_data = structured_lines[i]
        line_text = line_data.get('text', '').strip()
        if not line_text:
            continue

        # Determine if this line starts a new paragraph
        is_new_paragraph = False
        if i > 0:
            # Get the bottom of the previous line of text
            prev_line_y1 = structured_lines[i-1].get('y1')
            # Get the top of the current line of text
            current_line_y0 = line_data.get('y0')
            
            if prev_line_y1 is not None and current_line_y0 is not None:
                # Use font size of previous line as a reference for the expected line gap
                prev_font_size = structured_lines[i-1].get('size', 10)
                if prev_font_size <= 0: prev_font_size = 10

                gap = current_line_y0 - prev_line_y1
                
                # A gap larger than half the font size likely indicates a paragraph break.
                if gap > (prev_font_size * 0.5):
                    is_new_paragraph = True
        
        # If it's a new paragraph, finalize the previous one and start a new one
        if is_new_paragraph and current_paragraph_lines:
            paragraphs.append(" ".join(current_paragraph_lines))
            current_paragraph_lines = [line_text]
        else:
            current_paragraph_lines.append(line_text)

    # Add the last paragraph
    if current_paragraph_lines:
        paragraphs.append(" ".join(current_paragraph_lines))

    # Step 2: Join paragraphs and perform final cleaning
    full_text = "\n\n".join(paragraphs)

    # Remove lines that consist only of digits (likely page numbers)
    lines = full_text.split('\n')
    cleaned_lines = [line for line in lines if not line.strip().isdigit()]
    cleaned_text = "\n".join(cleaned_lines)
    
    # Normalize multiple newlines to a maximum of two
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # Remove lingering problematic characters
    cleaned_text = cleaned_text.encode('utf-8', 'ignore').decode('utf-8')

    return cleaned_text.strip()