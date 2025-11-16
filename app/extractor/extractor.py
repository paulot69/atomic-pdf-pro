import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

def _extract_text_with_pymupdf(pdf_path):
    """Extracts text from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    pages_text = [page.get_text() for page in doc]
    doc.close()
    return pages_text

def _extract_text_with_ocr(pdf_path):
    """Extracts text from a PDF using OCR."""
    images = convert_from_path(pdf_path)
    pages_text = [pytesseract.image_to_string(image) for image in images]
    return pages_text

def extract_text(pdf_path):
    """
    Extracts text from a PDF, falling back to OCR if necessary.
    """
    # Attempt to extract text with PyMuPDF
    pages_text = _extract_text_with_pymupdf(pdf_path)

    # Check if the extracted text is minimal
    total_text = "".join(pages_text)
    if len(total_text.strip()) < 500:
        print("Minimal text extracted. Falling back to OCR...")
        pages_text = _extract_text_with_ocr(pdf_path)

    return pages_text
