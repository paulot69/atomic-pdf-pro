import fitz

def create_simple_pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Capítulo 1: Introducción\n\nEste es el contenido del primer capítulo.", fontsize=12)
    page.insert_text((50, 200), "Capítulo 2: Desarrollo\n\nEste es el contenido del segundo capítulo.", fontsize=12)
    doc.save(path)
    doc.close()

if __name__ == "__main__":
    create_simple_pdf("tests/fixtures/sample.pdf")
