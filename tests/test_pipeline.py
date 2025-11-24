import pytest
from pathlib import Path
from pdf_atomic_pro.core import pipeline
from pdf_atomic_pro.core.estructura.indice_detector import TOCEntry

# Datos de prueba simulados que devolvería el extractor de texto
MOCK_STRUCTURED_TEXT = [
    [  # Página 1
        {"text": "Capítulo 1: El Comienzo", "font": "Arial", "size": 14.0, "is_bold": True},
        {"text": "Este es el primer párrafo.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
    ],
    [  # Página 2
        {"text": "Este es el segundo párrafo en otra página.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
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
        return_value=[TOCEntry(title="Capítulo 1: El Comienzo", page_number=1)]
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
    # Nota: El pipeline sanitiza los nombres (reemplaza espacios por guiones, quita acentos, etc.)
    # "Mi Libro de Prueba" -> "Mi-Libro-de-Prueba"
    # "Un Autor" -> "Un-Autor"
    sanitized_title = "Mi-Libro-de-Prueba"
    sanitized_author = "Un-Autor"

    book_root_path = output_dir / f"{year} - {sanitized_title} - {sanitized_author}"
    assert book_root_path.exists(), f"La carpeta raíz del libro no fue creada en: {book_root_path}"
    
    # Verificamos que se haya creado el MOC principal
    # El formato es "{titulo} {año} - {autor}.md"
    main_moc_filename = f"{book_title} {year} - {author}.md"
    main_moc_path = book_root_path / main_moc_filename
    assert main_moc_path.exists(), f"El MOC principal no fue creado en: {main_moc_path}"

    # Verificamos la creación de la carpeta del capítulo
    # Buscamos *cualquier* carpeta que empiece con "Capítulo 01 -"
    chapter_folders = list(book_root_path.glob("Capítulo 01 - *"))
    assert len(chapter_folders) > 0, "La carpeta del capítulo no fue creada."
    chapter_folder_path = chapter_folders[0]

    # Verificamos la creación de una nota atómica
    # Buscamos cualquier archivo .md dentro de la carpeta del capítulo que NO sea un MOC
    md_files = [f for f in chapter_folder_path.glob("*.md") if not f.name.startswith("MOC -")]
    assert len(md_files) > 0, "No se encontraron notas atómicas en la carpeta del capítulo."
    
    # Verificamos que el MOC del capítulo NO exista (porque solo hay 1 nota)
    # Según la lógica en mocs.py: if len(chapter_data.get('atomic_notes', [])) > 1: ...
    chapter_mocs = list(chapter_folder_path.glob("MOC - *.md"))
    assert len(chapter_mocs) == 0, "Se creó un MOC de capítulo innecesario para un capítulo con una sola nota."