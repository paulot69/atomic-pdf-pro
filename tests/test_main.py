import os
import sys
import shutil
import pytest
import fitz  # PyMuPDF
import yaml
from pathlib import Path

# Añadir el directorio raíz del proyecto al path de Python para encontrar 'main'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main as cli_main


# --- Fixtures para crear el entorno de prueba ---

@pytest.fixture(scope="module")
def test_environment():
    """Crea un entorno de prueba con un PDF de ejemplo y un directorio de salida."""
    test_dir = Path("tests/test_workspace")
    output_dir = test_dir / "output"
    pdf_path = test_dir / "ejemplo.pdf"

    # Crear directorios
    test_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # --- Crear un PDF de prueba con PyMuPDF ---
    doc = fitz.open()

    # Página 1: Capítulo 1
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Capítulo 1: La Aventura", fontsize=20)
    page1.insert_text((72, 108), "Este es el contenido del primer capítulo. Habla sobre [[Concepto Clave]].")

    # Página 2: Capítulo 2
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Capítulo 2: El Descubrimiento", fontsize=20)
    page2.insert_text((72, 108), "Este es el contenido del segundo capítulo. Menciona el [[Concepto Clave]] otra vez.")
    page2.insert_text((72, 144), "Y aquí se habla de una [[Nota Especial]].")

    # Añadir bookmarks para simular el índice
    toc = [
        [1, "Capítulo 1: La Aventura", 1],
        [1, "Capítulo 2: El Descubrimiento", 2]
    ]
    doc.set_toc(toc)

    # Guardar el PDF
    doc.save(str(pdf_path))
    doc.close()

    # Proporcionar las rutas al test
    yield {"pdf_path": str(pdf_path), "output_dir": str(output_dir)}

    # --- Limpieza después de las pruebas ---
    shutil.rmtree(test_dir)

# --- Test principal de la aplicación ---

def test_full_pipeline(test_environment, monkeypatch):
    """
    Ejecuta el pipeline completo y verifica los resultados.
    """
    pdf_path = test_environment["pdf_path"]
    output_dir = test_environment["output_dir"]

    # --- Simular argumentos de línea de comandos ---
    # Usamos monkeypatch para simular sys.argv
    test_args = [
        "main.py",
        pdf_path,
        "--salida",
        output_dir,
        "--titulo",
        "Libro de Prueba",
        "--autor",
        "Jules Verne",
        "--ano",
        "2025"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    # --- Ejecutar el programa ---
    cli_main.main()

    # --- Verificaciones ---

    # 1. Verificar que se creó la carpeta del libro
    expected_book_folder_name = "2025 - Libro-de-Prueba - Jules-Verne"
    book_folder_path = Path(output_dir) / expected_book_folder_name
    assert book_folder_path.is_dir(), f"No se encontró la carpeta del libro: {book_folder_path}"

    # 2. Verificar la existencia del MOC principal
    expected_main_moc = book_folder_path / "MOC - Libro-de-Prueba.md"
    assert expected_main_moc.is_file(), "No se encontró el MOC principal."

    # 3. Verificar la estructura de capítulos y la validez del YAML en cada nota
    all_md_files = list(book_folder_path.rglob("*.md"))
    assert len(all_md_files) > 2, "No se generaron suficientes archivos Markdown."

    for md_file in all_md_files:
        # No verificamos el YAML de los MOCs, solo de las notas atómicas
        if "MOC" not in md_file.name:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Verificar que el frontmatter YAML sea válido
                try:
                    yaml_content = content.split("---")[1]
                    yaml_data = yaml.safe_load(yaml_content)
                    assert isinstance(yaml_data, dict), f"El YAML en {md_file} no es un diccionario válido."
                    assert "tags" in yaml_data, f"Faltan 'tags' en el YAML de {md_file}."
                except (yaml.YAMLError, IndexError) as e:
                    pytest.fail(f"Error al parsear el YAML en {md_file}: {e}")

    # 4. Verificar que no haya enlaces rotos
    # (El propio programa ya hace esto, pero podemos añadir una aserción aquí
    # si modificamos el verificador para que devuelva un estado)
    # Por ahora, confiamos en el log del programa. Podemos mejorarlo si es necesario.
    # Esta es una verificación implícita de que el programa terminó con éxito (código 0).
