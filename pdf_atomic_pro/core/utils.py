import os

def find_pdf_recursive(pdf_name, base_path="/input"):
    for root, dirs, files in os.walk(base_path):
        if pdf_name in files:
            return os.path.join(root, pdf_name)
    return None
