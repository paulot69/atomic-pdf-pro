import os

def find_pdf_recursive(pdf_name, base_path="/input"):
    """
    Busca recursivamente un archivo PDF en el path base dado.
    Retorna la ruta completa si lo encuentra, o None si no.
    No imprime nada ni lanza excepciones.
    """
    try:
        for root, dirs, files in os.walk(base_path):
            if pdf_name in files:
                return os.path.join(root, pdf_name)
    except Exception:
        pass
    return None
