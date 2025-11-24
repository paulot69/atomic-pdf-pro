import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pdf_atomic_pro.core.estructura.indice_detector import TOCEntry, detect_toc_entries, detect_toc_from_bookmarks
from pdf_atomic_pro.core.estructura.jerarquia import split_into_chapters, split_chapter_into_sections
from pdf_atomic_pro.core.limpieza.normalizador import normalize_text
from pdf_atomic_pro.core.utils.config_loader import load_config

# --- Fixtures for reusable test data ---

@pytest.fixture
def mock_config():
    """Returns a mock configuration dictionary for subtitle detection."""
    return {
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
        }
    }

@pytest.fixture
def sample_structured_text_with_toc():
    """Structured text representing a PDF with a clear TOC at the beginning."""
    return [
        [ # Page 1: TOC
            {"text": "Tabla de Contenido", "font": "Arial", "size": 18.0, "is_bold": True},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "Capítulo 1. Introducción............... 10", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "  1.1. Fundamentos....................... 12", "font": "Arial", "size": 10.0, "is_bold": False},
            {"text": "    1.1.1. Orígenes...................... 13", "font": "Arial", "size": 10.0, "is_bold": False},
            {"text": "Capítulo 2. Desarrollo................. 20", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
        ],
        [ # Page 2: Chapter 1 start
            {"text": "Capítulo 1: Introducción", "font": "Arial", "size": 14.0, "is_bold": True},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "Este es el texto introductorio del capítulo 1.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "1.1. Fundamentos", "font": "Arial", "size": 13.0, "is_bold": True},
            {"text": "Aquí se detallan los fundamentos del tema.", "font": "Times New Roman", "size": 11.0, "is_bold": False},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "    1.1.1. Orígenes", "font": "Arial", "size": 12.0, "is_bold": True},
            {"text": "Los orígenes son complejos.", "font": "Times New Roman", "size": 11.0, "is_bold": False},
        ],
        [ # Page 3: Chapter 2 start (page 20 in PDF logic, but page 3 in 0-indexed structured_text)
            {"text": "Capítulo 2: Desarrollo", "font": "Arial", "size": 14.0, "is_bold": True},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "El desarrollo del tema es extenso.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
        ]
    ]

@pytest.fixture
def sample_structured_text_no_toc():
    """Structured text without an explicit TOC section, but with font-based headers."""
    return [
        [ # Page 1
            {"text": "UN TITULO GRANDE", "font": "Arial", "size": 16.0, "is_bold": True},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "Texto normal del primer capítulo.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "Una Sección Importante", "font": "Arial", "size": 13.0, "is_bold": True},
            {"text": "Contenido de la sección importante.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
        ],
        [ # Page 2
            {"text": "OTRO CAPITULO", "font": "Arial", "size": 16.0, "is_bold": True},
            {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "Más texto normal para el segundo capítulo.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
        ]
    ]

# --- Tests for indice_detector.py ---

def test_detect_toc_entries_with_explicit_toc_text(sample_structured_text_with_toc):
    """Test TOC detection from text, including indentation-based levels."""
    toc_entries = detect_toc_entries(sample_structured_text_with_toc)
    
    assert len(toc_entries) == 4
    assert toc_entries[0].raw_title == "Capítulo 1. Introducción..............."
    assert toc_entries[0].title == "Introducción"
    assert toc_entries[0].page_number == 10
    assert toc_entries[0].level == 1 # Top level
    
    assert toc_entries[1].raw_title == "  1.1. Fundamentos......................." # Retained leading spaces
    assert toc_entries[1].title == "1.1. Fundamentos"
    assert toc_entries[1].page_number == 12
    assert toc_entries[1].level == 2 # Indented
    
    assert toc_entries[2].raw_title == "    1.1.1. Orígenes......................" # Retained leading spaces
    assert toc_entries[2].title == "1.1.1. Orígenes"
    assert toc_entries[2].page_number == 13
    assert toc_entries[2].level == 3 # Further indented

    assert toc_entries[3].raw_title == "Capítulo 2. Desarrollo................."
    assert toc_entries[3].title == "Desarrollo" # Corrected expected value
    assert toc_entries[3].page_number == 20
    assert toc_entries[3].level == 1 # Top level again

def test_detect_toc_entries_no_toc_found():
    """Test that detect_toc_entries returns empty if no valid TOC lines are found."""
    structured_text = [
        [{"text": "Random text here.", "font": "Arial", "size": 12.0, "is_bold": False}]
    ]
    toc_entries = detect_toc_entries(structured_text)
    assert not toc_entries

def test_detect_toc_from_bookmarks_mocked(mocker):
    """Test bookmark-based TOC detection with a mock PDF."""
    mock_doc = MagicMock()
    mock_doc.get_toc.return_value = [
        [1, "Capítulo 1", 5],
        [2, "Sección 1.1", 7]
    ]
    mocker.patch('fitz.open', return_value=mock_doc)
    
    entries = detect_toc_from_bookmarks("dummy_path.pdf")
    assert len(entries) == 2
    assert entries[0].title == "Capítulo 1"
    assert entries[0].page_number == 5
    assert entries[0].level == 1

# --- Tests for jerarquia.py ---

def test_split_into_chapters_with_toc(sample_structured_text_with_toc, mock_config):
    """Test split_into_chapters uses TOC entries when provided."""
    toc_entries = detect_toc_entries(sample_structured_text_with_toc) # Use the real detector
    chapters = split_into_chapters(sample_structured_text_with_toc, toc_entries, mock_config)

    assert len(chapters) == 4 # Expect 4 chapters/sections as per TOC entries
    assert chapters[0]['title'] == "Capítulo 1: Introducción"
    assert chapters[0]['number'] == 1
    assert chapters[0]['level'] == 1
    assert len(chapters[0]['sections']) > 0 # Should have content from Chapter 1.
    
    assert chapters[1]['title'] == "1.1. Fundamentos"
    assert chapters[1]['number'] == 2
    assert chapters[1]['level'] == 2
    assert len(chapters[1]['sections']) > 0 # Should have content from 1.1. Fundamentos
    
    assert chapters[2]['title'] == "1.1.1. Orígenes"
    assert chapters[2]['number'] == 3
    assert chapters[2]['level'] == 3
    assert len(chapters[2]['sections']) > 0 # Should have content from 1.1.1. Orígenes

    assert chapters[3]['title'] == "Capítulo 2: Desarrollo"
    assert chapters[3]['number'] == 4
    assert chapters[3]['level'] == 1
    assert len(chapters[3]['sections']) > 0 # Should have content from Chapter 2.


def test_split_into_chapters_fallback_mode(sample_structured_text_no_toc, mock_config):
    """Test split_into_chapters falls back to heuristics when no TOC entries are provided."""
    chapters = split_into_chapters(sample_structured_text_no_toc, [], mock_config) # No TOC entries passed

    assert len(chapters) == 2
    assert chapters[0]['title'] == "UN TITULO GRANDE"
    assert chapters[0]['number'] == 1
    assert len(chapters[0]['sections']) >= 1 # Should split into "Una Sección Importante"

    assert chapters[1]['title'] == "OTRO CAPITULO"
    assert chapters[1]['number'] == 2
    assert len(chapters[1]['sections']) == 1

def test_split_into_chapters_single_chapter_fallback(mock_config):
    """Test split_into_chapters treats entire document as single chapter if no headers found."""
    structured_text = [
        [
            {"text": "Just some plain text.", "font": "Arial", "size": 12.0, "is_bold": False},
            {"text": "More plain text.", "font": "Arial", "size": 12.0, "is_bold": False},
        ]
    ]
    chapters = split_into_chapters(structured_text, [], mock_config) # No TOC, no heuristic headers

    assert len(chapters) == 1
    assert chapters[0]['title'] == "Contenido Completo"
    assert len(chapters[0]['sections']) == 1
    assert "Just some plain text." in chapters[0]['sections'][0]['content']

def test_split_chapter_into_sections_config_driven(mock_config):
    """Test split_chapter_into_sections uses config-driven heuristics."""
    chapter_content = [
        {"text": "Normal paragraph text.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
        {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
        {"text": "1.2. Un Subtítulo Importante", "font": "Arial", "size": 13.5, "is_bold": True}, # Score: 2 (bold) + 2 (font size > 1.15) + 2 (numbering) + 1 (short) + 1 (ends like title) = 8
        {"text": "Contenido del subtítulo.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
        {"text": " ", "font": "Arial", "size": 12.0, "is_bold": False},
        {"text": "Otro Subtítulo", "font": "Arial", "size": 13.0, "is_bold": False}, # Score: 1 (font size > 1.05) + 1 (short) + 1 (ends like title) = 3 (threshold is 3)
        {"text": "Más contenido.", "font": "Times New Roman", "size": 12.0, "is_bold": False},
    ]
    # Dominant style: Times New Roman, 12.0pt, not bold
    # The first text line has size 12.0, is_bold=False
    # The subtitle "1.2. Un Subtítulo Importante" has size 13.5 (13.5/12 = 1.125, so not strong, but weak), is_bold=True
    # The subtitle "Otro Subtítulo" has size 13.0 (13.0/12 = 1.08, so weak), is_bold=False

    sections = split_chapter_into_sections(chapter_content, "Título del Capítulo", mock_config)

    assert len(sections) == 3
    assert sections[0]['title'] == "Título del Capítulo"
    assert "Normal paragraph text." in sections[0]['content']
    assert sections[1]['title'] == "1.2. Un Subtítulo Importante"
    assert "Contenido del subtítulo." in sections[1]['content']
    assert sections[2]['title'] == "Otro Subtítulo"
    assert "Más contenido." in sections[2]['content']

def test_split_chapter_into_sections_no_subtitles(mock_config):
    """Test split_chapter_into_sections returns single section if no subtitles found."""
    chapter_content = [
        {"text": "Just plain text.", "font": "Arial", "size": 12.0, "is_bold": False},
        {"text": "More plain text.", "font": "Arial", "size": 12.0, "is_bold": False},
    ]
    sections = split_chapter_into_sections(chapter_content, "Simple Chapter", mock_config)
    assert len(sections) == 1
    assert sections[0]['title'] == "Simple Chapter"
    assert "Just plain text." in sections[0]['content']
