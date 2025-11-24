import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pdf_atomic_pro.core import pipeline
from pdf_atomic_pro.core.estructura.indice_detector import TOCEntry
from pdf_atomic_pro.core.generacion.utils import _sanitize_title_for_filename

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

# Mock template content
# Updated: Quoted the title to prevent YAML parsing errors with colons
MOCK_ATOMIC_NOTE_TEMPLATE = """---
tags:
  - test/tag
  - fuente/{{ author_lastname }}
title: "{{ note_title }}"
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

def test_process_pdf_full_pipeline(mocker, tmp_path):
    """
    Prueba el pipeline de extremo a extremo, simulando la extracción de texto
    y el cargador de configuración para un control total.
    """
    # 1. Preparación (Arrange)
    
    # Create real template files in tmp_path
    templates_dir = tmp_path / "config" / "templates"
    templates_dir.mkdir(parents=True)
    
    atomic_note_path = templates_dir / "atomic_note.md"
    atomic_note_path.write_text(MOCK_ATOMIC_NOTE_TEMPLATE, encoding='utf-8')
    
    chapter_moc_path = templates_dir / "chapter_moc.md"
    chapter_moc_path.write_text(MOCK_CHAPTER_MOC_TEMPLATE, encoding='utf-8')

    book_moc_path = templates_dir / "book_moc.md"
    book_moc_path.write_text(MOCK_BOOK_MOC_TEMPLATE, encoding='utf-8')
    
    # Mock configuration pointing to REAL temporary files
    mock_config = {
        'structure': {
            'book_folder_name': "{year} - {title} - {author}",
            'chapter_folder_name': "C - {chapter_number:02d} - {chapter_title}",
            'atomic_note_name': "{chapter_number}.{note_number} - {note_title}",
            'book_moc_name': "MOC - {title}.md",
            'chapter_moc_name': "MOC_Cap_{chapter_number:02d}_{chapter_title}.md"
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
            'atomic_note': str(atomic_note_path),
            'chapter_moc': str(chapter_moc_path),
            'book_moc': str(book_moc_path),
        }
    }

    # Mock config loader in the pipeline module OBJECT
    mocker.patch.object(pipeline, "load_config", return_value=mock_config)

    # Mock text extraction
    mocker.patch(
        "pdf_atomic_pro.core.extractor.pdf_reader.extract_text_with_pymupdf", 
        return_value=MOCK_STRUCTURED_TEXT
    )
    
    # Mock bookmark TOC detection
    mocker.patch(
        "pdf_atomic_pro.core.estructura.indice_detector.detect_toc_from_bookmarks",
        return_value=[]
    )

    # Mock TOC entry detection
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
    author = "Un Autor Largo"
    year = "2025"

    # 2. Actuación (Act)
    result = pipeline.process_pdf(
        pdf_path=pdf_path,
        title=book_title,
        author=author,
        year=year,
        output_dir=output_dir,
        use_ai=False,
        generate_summaries=False
    )

    # 3. Verificación (Assert)
    assert result is True, "El pipeline debería finalizar con éxito."

    # Verify book root path
    sanitized_title = _sanitize_title_for_filename(book_title)
    sanitized_author = _sanitize_title_for_filename(author)
    book_root_path_expected_name = mock_config['structure']['book_folder_name'].format(
        year=year, title=sanitized_title, author=sanitized_author
    )
    book_root_path = output_dir / book_root_path_expected_name
    assert book_root_path.exists(), f"La carpeta raíz del libro no fue creada en: {book_root_path}"
    
    # Verify main MOC creation
    main_moc_filename_expected = mock_config['structure']['book_moc_name'].format(title=sanitized_title)
    main_moc_path = book_root_path / main_moc_filename_expected
    assert main_moc_path.exists(), f"El MOC principal no fue creado en: {main_moc_path}"
    
    # Verify chapter folder
    # NOTE: The pipeline (jerarquia.py) uses the title found in the text ("Capítulo 1: El Comienzo"), not the cleaned TOC title ("El Comienzo").
    # This results in the folder name containing "Capítulo-1-El-Comienzo".
    chapter_1_title_raw = "Capítulo 1: El Comienzo"
    chapter_folders = list(book_root_path.glob(f"C - 01 - {_sanitize_title_for_filename(chapter_1_title_raw)}"))
    assert len(chapter_folders) > 0, f"La carpeta del Capítulo 1 no fue creada o no se encontró. Esperado: C - 01 - {_sanitize_title_for_filename(chapter_1_title_raw)}"
    chapter_1_path = chapter_folders[0]

    # Verify atomic note
    # Same logic applies to note title
    atomic_note_1_title = "Capítulo 1: El Comienzo"
    atomic_note_1_filename_expected = mock_config['structure']['atomic_note_name'].format(
        chapter_number=1, note_number=1, note_title=_sanitize_title_for_filename(atomic_note_1_title)
    )
    atomic_note_1_path = chapter_1_path / f"{atomic_note_1_filename_expected}.md"
    assert atomic_note_1_path.exists(), f"Nota atómica 1.1 no creada: {atomic_note_1_path}"

    # Verify content of atomic note 1
    atomic_note_1_content = atomic_note_1_path.read_text(encoding='utf-8')
    assert f'title: "{atomic_note_1_title}"' in atomic_note_1_content # Check YAML title (quoted)
    assert f"# {atomic_note_1_title}" in atomic_note_1_content # Check Markdown H1
    # Check note content - Use a partial match because 'jerarquia' or 'notas_atomicas' might clean/merge lines differently
    # The debug output shows the chapter was treated as a single note, so it should contain the concatenated text.
    assert "Este es el primer párrafo." in atomic_note_1_content
    assert f"test/tag" in atomic_note_1_content
    assert f"fuente/largo" in atomic_note_1_content
