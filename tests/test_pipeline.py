import pytest
from pathlib import Path
from pdf_atomic_pro.core import pipeline

# Datos de prueba simulados que devolvería el extractor de texto
MOCK_STRUCTURED_TEXT = [
    [  # Página 1
        {"text": "Capítulo 1: El Comienzo"},
        {"text": "Este es el primer párrafo."},
    ],
    [  # Página 2
        {"text": "Este es el segundo párrafo en otra página."},
    ]
]

# Usamos 'mocker' para simular la extracción de texto y 'tmp_path' para un directorio temporal.
def test_process_pdf_full_pipeline(mocker, tmp_path):
    """
    Prueba el pipeline de extremo a extremo, simulando la extracción de texto
    para evitar la dependencia de un motor de PDF real en la prueba.
    """
    # 1. Preparación (Arrange)
    
    # Simulamos (mock) la función de extracción de texto para que devuelva nuestro texto falso.
    mocker.patch(
        "pdf_atomic_pro.core.extractor.pdf_reader.extract_text_with_pymupdf", 
        return_value=MOCK_STRUCTURED_TEXT
    )
    
    # Simulamos el detector de TOC para que devuelva un capítulo simple.
    mocker.patch(
        "pdf_atomic_pro.core.estructura.indice_detector.detect_toc_entries",
        return_value=[("Capítulo 1: El Comienzo", 1)]
    )

    pdf_path = "tests/assets/sample.pdf"
    output_dir = tmp_path
    book_title = "Mi Libro de Prueba"
    author = "Un Autor"
    year = "2025"

    # 2. Actuación (Act)
    result = pipeline.process_pdf(
        pdf_path=pdf_path,
        title=book_title,
        author=author,
        year=year,
        output_dir=output_dir,
        use_ai=False,          # Desactivar IA para pruebas predecibles y rápidas
        generate_summaries=False
    )

    # 3. Verificación (Assert)
    assert result is True, "El pipeline debería finalizar con éxito."

    # Verificamos que se haya creado la carpeta principal del libro
    book_root_path = output_dir / f"{year} - {book_title} - {author}"
    assert book_root_path.exists(), "La carpeta raíz del libro no fue creada."
    
    # Verificamos que se haya creado el MOC principal
    main_moc_path = book_root_path / f"MOC - {book_title}.md"
    assert main_moc_path.exists(), "El MOC principal no fue creado."

    # Verificamos la creación de la carpeta del capítulo
    chapter_folder_path = book_root_path / "Capitulo 01 - El Comienzo"
    assert chapter_folder_path.exists(), "La carpeta del capítulo no fue creada."

    # Verificamos la creación de una nota atómica
    # Buscamos cualquier archivo .md dentro de la carpeta del capítulo
    md_files = list(chapter_folder_path.glob("*.md"))
    assert len(md_files) > 0, "No se encontraron notas atómicas en la carpeta del capítulo."
    
    # Verificamos que el MOC del capítulo exista
    chapter_moc_path = chapter_folder_path / "MOC - Capitulo 01 - El Comienzo.md"
    assert chapter_moc_path.exists(), "El MOC del capítulo no fue creado."