from pdf2image import convert_from_path
import pytesseract

def extract_text_with_ocr(pdf_path):
    """Extracts text from a PDF using OCR."""
    images = convert_from_path(pdf_path)
    # Convert OCR plain text to structured format with default font info
    structured_pages_text = []
    for image in images:
        page_text = pytesseract.image_to_string(image)
        page_lines = []
        for line in page_text.split('\n'):
            if line.strip():
                page_lines.append({"text": line.strip(), "size": 12.0, "is_bold": False, "y0": 0, "y1": 0}) # Default font info
        structured_pages_text.append(page_lines)
    return structured_pages_text
