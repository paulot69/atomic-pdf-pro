import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pdf_atomic_pro.core import pipeline
from pdf_atomic_pro.core.estructura.indice_detector import TOCEntry
from pdf_atomic_pro.core.generacion.utils import _sanitize_title_for_filename # Import to get sanitized names
from jinja2 import Template # Import Jinja2 Template

# Datos de prueba simulados que devolvería el extractor de texto
MOCK_STRUCTURED_TEXT = [
    [  # Página 1
        {"text": "Capítulo 1: El Comienzo", "font": "Arial", "size": 14.0, "is_bold": True, "original_page_number": 1},
        {"text": "Este es el primer párrafo.", "font": "Times New Roman", "size": 12.0, "is_bold": False, "original_page_number": 1},
        {"text": "Subsección 1.1", "font": "Arial", "size": 13.0, "is_bold": True, "original_page_number": 1},
        {"text": "Contenido de la subsección.", "font": "Times New Roman", "size": 12.0, "is_bold": False, "original_page_number": 1},
    ],
    [  # Página 2
        {"text": "Capítulo 2: El Final", "font": "Arial", "size": 14.0, "is_bold": True, "original_page_number": 2},
        {"text": "Este es el segundo párrafo en otra página.", "font": "Times New Roman", "size": 12.0, "is_bold": False, "original_page_number": 2},
    ]
]

# Mock configuration for the pipeline
MOCK_CONFIG = {
    'structure': {
        'book_folder_name': "{year} - {title} - {author}",
        'chapter_folder_name': "C - {chapter_number:02d} - {chapter_title}", # Simplified for test
        'atomic_note_name': "{chapter_number}.{note_number} - {note_title}",
        'book_moc_name': "MOC - {title}.md", # CORRECTED to match config/rules.yaml
        'chapter_moc_name': "MOC_Cap_{chapter_number:02d}_{chapter_title}.md" # Simplified for test
    },
    'subtitle_detection': {
        'threshold': 3,
        'heuristics': {
            'bold_vs_not_bold': {'score': 2},
            'font_size_increase_strong': {'multiplier': 1.15, 'score': 2},
            'font_size_increase_weak': {'multiplier': 1.05, 'score': 1},
            'is_short': {'score': 1},
            'ends_like_title': {'score': 1},
            'numbering_pattern': {'regex': r"^\s*(\d+(\.\d+)*|[a-zA-Z]\)|[ivxlcdm]+\.)\s+.*", 'score': 2}
        }
    },
    'templates': {
        'atomic_note': "config/templates/atomic_note_template.md",
        'chapter_moc': "config/templates/chapter_moc_template.md",
        'book_moc': "config/templates/book_moc_template.md",
    }
}

# Mock template content
MOCK_ATOMIC_NOTE_TEMPLATE = """---
tags:
  - test/tag
  - fuente/{{ author_lastname }}
title: {{ note_title }}
---
# {{ note_title }}
Content: {{ note_content }}
Footer: {{ chapter_moc_filename }} | {{ book_moc_filename }}
"""
MOCK_CHAPTER_MOC_TEMPLATE = """# MOC Chapter {{ chapter_number }} - {{ chapter_title }}
Link to book: {{ book_moc_filename }}
"""
MOCK_BOOK_MOC_TEMPLATE = """# MOC Book {{ book_title }}
"""

# Usamos 'mocker' para simular la extracción de texto y 'tmp_path' para un directorio temporal.
def test_process_pdf_full_pipeline(mocker, tmp_path):
    """
    Prueba el pipeline de extremo a extremo, simulando la extracción de texto
    y el cargador de configuración para un control total.
    """
    # 1. Preparación (Arrange)
    
    # Mock config loader in all relevant namespaces where it might be called
    mocker.patch("pdf_atomic_pro.core.pipeline.load_config", return_value=MOCK_CONFIG)
    mocker.patch("pdf_atomic_pro.core.estructura.jerarquia.load_config", return_value=MOCK_CONFIG) # For jerarquia's fallback
    mocker.patch("pdf_atomic_pro.core.generacion.notas_atomicas.load_config", return_value=MOCK_CONFIG) # For notas_atomicas's fallback
    mocker.patch("pdf_atomic_pro.core.generacion.mocs.load_config", return_value=MOCK_CONFIG) # For mocs's fallback

    # Mock template file reading (Path.open) and Jinja2 Template constructor
    mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())
    
    # Mock Jinja2 Template constructor to return a mock object with a controlled render method
    mock_jinja_template_init = mocker.patch("jinja2.Template", autospec=True)
    
    # Configure the mock Template instances for each template path
    def get_mock_template_instance(template_string):
        mock_instance = MagicMock(spec=Template)
        mock_instance.render.side_effect = lambda context: template_string.replace('{{ note_title }}', context.get('note_title', '')) \
                                                        .replace('{{ note_content }}', context.get('note_content', '')) \
                                                        .replace('{{ author_lastname }}', context.get('author_lastname', '')) \
                                                        .replace('{{ chapter_moc_filename }}', context.get('chapter_moc_filename', '')) \
                                                        .replace('{{ book_moc_filename }}', context.get('book_moc_filename', '')) \
                                                        .replace('{{ chapter_number }}', str(context.get('chapter_number', ''))) \
                                                        .replace('{{ chapter_title }}', context.get('chapter_title', '')) \
                                                        .replace('{{ book_title }}', context.get('book_title', ''))
        return mock_instance

    # When Jinja2.Template() is called, return our controlled mock
    mock_jinja_template_init.side_effect = [
        get_mock_template_instance(MOCK_ATOMIC_NOTE_TEMPLATE),  # For atomic note template
        get_mock_template_instance(MOCK_CHAPTER_MOC_TEMPLATE),  # For chapter MOC template
        get_mock_template_instance(MOCK_BOOK_MOC_TEMPLATE)      # For book MOC template
    ]
    
    # Simulamos la función de extracción de texto para que devuelva nuestro texto falso.
    mocker.patch(
        "pdf_atomic_pro.core.extractor.pdf_reader.extract_text_with_pymupdf", 
        return_value=MOCK_STRUCTURED_TEXT
    )
    
    # Simulamos el detector de TOC para que devuelva entradas de TOC más completas.
    mocker.patch(
        "pdf_atomic_pro.core.estructura.indice_detector.detect_toc_entries",
        return_value=[
            TOCEntry(raw_title="Capítulo 1: El Comienzo", title="El Comienzo", page_number=1, level=1),
            TOCEntry(raw_title="Subsección 1.1", title="Subsección 1.1", page_number=1, level=2),
            TOCEntry(raw_title="Capítulo 2: El Final", title="El Final", page_number=2, level=1),
        ]
    )

    pdf_path = "tests/assets/sample.pdf"
    output_dir = tmp_path
    book_title = "Mi Libro de Prueba"
    author = "Un Autor Largo" # Changed to test _get_author_lastname
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

    # Verify book root path using config
    sanitized_title = _sanitize_title_for_filename(book_title)
    sanitized_author = _sanitize_title_for_filename(author)
    book_root_path_expected_name = MOCK_CONFIG['structure']['book_folder_name'].format(
        year=year, title=sanitized_title, author=sanitized_author
    )
    book_root_path = output_dir / book_root_path_expected_name
    assert book_root_path.exists(), f"La carpeta raíz del libro no fue creada en: {book_root_path}"
    
    # Verify main MOC creation using config
    main_moc_filename_expected = MOCK_CONFIG['structure']['book_moc_name'].format(title=sanitized_title)
    main_moc_path = book_root_path / main_moc_filename_expected
    assert main_moc_path.exists(), f"El MOC principal no fue creado en: {main_moc_path}"
    
    # Verify chapter folder and note creation using config
    chapter_1_title = "El Comienzo"
    # Use glob to robustly find the chapter folder
    chapter_folders = list(book_root_path.glob(f"C - 01 - {_sanitize_title_for_filename(chapter_1_title)}"))
    assert len(chapter_folders) > 0, "La carpeta del Capítulo 1 no fue creada o no se encontró."
    chapter_1_path = chapter_folders[0]

    atomic_note_1_title = "El Comienzo"
    atomic_note_1_filename_expected = MOCK_CONFIG['structure']['atomic_note_name'].format(
        chapter_number=1, note_number=1, note_title=_sanitize_title_for_filename(atomic_note_1_title)
    )
    atomic_note_1_path = chapter_1_path / f"{atomic_note_1_filename_expected}.md"
    assert atomic_note_1_path.exists(), f"Nota atómica 1.1 no creada: {atomic_note_1_path}"

    # Verify content of atomic note 1
    atomic_note_1_content = atomic_note_1_path.read_text(encoding='utf-8')
    assert f"title: {atomic_note_1_title}" in atomic_note_1_content # Check YAML title
    assert f"# {atomic_note_1_title}" in atomic_note_1_content # Check Markdown H1
    assert "Content: Capítulo 1: El ComienzoEste es el primer párrafo." in atomic_note_1_content # Check note content
    assert "Footer: C - 01 - El-Comienzo/MOC_Cap_01_El-Comienzo.md | MOC_Libro_Mi-Libro-de-Prueba.md" in atomic_note_1_content # Check footer from template
    assert f"test/tag" in atomic_note_1_content # Check for a tag from template
    assert f"fuente/largo" in atomic_note_1_content # Check for author lastname tag

    # Verify chapter MOC for chapter 1 (should be created as there's more than one note effectively)
    chapter_1_moc_filename_expected = MOCK_CONFIG['structure']['chapter_moc_name'].format(
        chapter_number=1, chapter_title=_sanitize_title_for_filename(chapter_1_title)
    )
    chapter_1_moc_path = chapter_1_path / chapter_1_moc_filename_expected
    assert chapter_1_moc_path.exists(), f"MOC de Capítulo 1 no creado: {chapter_1_moc_path}"
    chapter_1_moc_content = chapter_1_moc_path.read_text(encoding='utf-8')
    assert f"# MOC Chapter 1 - {chapter_1_title}" in chapter_1_moc_content
    assert f"Link to book: {main_moc_filename_expected}" in chapter_1_moc_content

    # Clean up (handled by tmp_path fixture)