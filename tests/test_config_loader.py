import pytest
from pathlib import Path
import yaml
from pdf_atomic_pro.core.utils.config_loader import load_config

# Define a path to a temporary config directory for tests
@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

# Test loading a valid configuration
def test_load_valid_config(temp_config_dir):
    valid_config_content = """
    structure:
      book_folder_name: "{year} - {title} - {author}"
      chapter_folder_name: "Capítulo {chapter_number:02d} - {chapter_title}"
      atomic_note_name: "{chapter_number}.{note_number} - {note_title}"
      book_moc_name: "MOC - {title}.md"
      chapter_moc_name: "MOC - Capítulo {chapter_number:02d} - {chapter_title}.md"
    subtitle_detection:
      threshold: 3
      heuristics:
        bold_vs_not_bold:
          score: 2
        font_size_increase_strong:
          multiplier: 1.15
          score: 2
        font_size_increase_weak:
          multiplier: 1.05
          score: 1
        is_short:
          score: 1
        ends_like_title:
          score: 1
        numbering_pattern:
            regex: |
              ^\\s*(\\d+(\\.\\d+)*|[a-zA-Z]\\)|[ivxlcdm]+\\.)\\s+.*
            score: 2
    templates:
      atomic_note: "config/templates/atomic_note_template.md"
      chapter_moc: "config/templates/chapter_moc_template.md"
      book_moc: "config/templates/book_moc_template.md"
    """
    config_file = temp_config_dir / "rules.yaml"
    config_file.write_text(valid_config_content, encoding='utf-8')

    config = load_config(config_file)
    assert isinstance(config, dict)
    assert 'structure' in config
    assert 'subtitle_detection' in config
    assert 'templates' in config
    assert config['subtitle_detection']['threshold'] == 3

# Test loading a non-existent configuration file
def test_load_non_existent_config():
    with pytest.raises(FileNotFoundError):
        load_config(Path("non_existent_path/rules.yaml"))

# Test loading an empty configuration file
def test_load_empty_config(temp_config_dir):
    config_file = temp_config_dir / "rules.yaml"
    config_file.write_text("", encoding='utf-8')
    with pytest.raises(ValueError, match="Configuration file is empty or invalid."):
        load_config(config_file)

# Test loading a configuration with missing required keys
def test_load_config_missing_keys(temp_config_dir):
    invalid_config_content = """
    structure:
      book_folder_name: "{year} - {title} - {author}"
    templates:
      atomic_note: "config/templates/atomic_note_template.md"
    """ # Missing subtitle_detection
    config_file = temp_config_dir / "rules.yaml"
    config_file.write_text(invalid_config_content, encoding='utf-8')
    with pytest.raises(ValueError, match="Configuration file is missing required key: 'subtitle_detection'"):
        load_config(config_file)

# Test loading an improperly formatted YAML file
def test_load_invalid_yaml_format(temp_config_dir):
    invalid_yaml_content = """
    structure:
      - item1
    key: value: "malformed string
    """ # Malformed YAML, now properly closed
    config_file = temp_config_dir / "rules.yaml"
    config_file.write_text(invalid_yaml_content, encoding='utf-8')
    with pytest.raises(ValueError, match="Error parsing configuration file"):
        load_config(config_file)

