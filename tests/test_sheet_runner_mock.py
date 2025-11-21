import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the root directory to sys.path so we can import sheet_runner
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sheet_runner
from sheet_runner import get_sheet_data, parse_toc_from_string, main as runner_main

class TestSheetRunner(unittest.TestCase):

    def setUp(self):
        # Mock data simulating Google Sheets response
        self.mock_sheet_values = [
            ['ATOMIZAR LIBRO', 'URL LOCAL', 'Título Original del Libro', 'Autor (Nombre Apellido)', 'Año de Publicación', 'INDICE'],
            ['SI', 'test_book.pdf', 'Test Book', 'Test Author', '2023', 'Chapter 1\n    Section 1.1'],
            ['NO', 'ignored_book.pdf', 'Ignored Book', 'Ignored Author', '2020', ''],
        ]

    def test_parse_toc_from_string(self):
        """Test parsing the TOC string from CSV into TOCEntry objects."""
        toc_str = "Chapter 1\n    Section 1.1\n        Subsection 1.1.1"
        entries = parse_toc_from_string(toc_str)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].title, "Chapter 1")
        self.assertEqual(entries[0].level, 1)
        self.assertEqual(entries[1].title, "Section 1.1")
        self.assertEqual(entries[1].level, 2)
        self.assertEqual(entries[2].title, "Subsection 1.1.1")
        self.assertEqual(entries[2].level, 3)

    @patch('sheet_runner.Credentials')
    @patch('sheet_runner.build')
    @patch('os.path.exists')
    @patch.dict(os.environ, {'SPREADSHEET_ID': 'mock_id'})
    def test_get_sheet_data(self, mock_exists, mock_build, mock_creds):
        """Test fetching and parsing data from Google Sheets."""
        # Setup mocks
        mock_exists.return_value = True # Pretend credentials file exists

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_sheet_api = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheet_api

        mock_values = MagicMock()
        mock_sheet_api.values.return_value = mock_values

        mock_get = MagicMock()
        mock_values.get.return_value = mock_get

        mock_get.execute.return_value = {'values': self.mock_sheet_values}

        # Execute
        data = get_sheet_data()

        # Assertions
        self.assertEqual(len(data), 2) # Header is consumed, 2 rows remaining
        self.assertEqual(data[0]['atomizar libro'], 'SI')
        self.assertEqual(data[0]['título original del libro'], 'Test Book')
        self.assertEqual(data[1]['atomizar libro'], 'NO')

    @patch('sheet_runner.get_sheet_data')
    @patch('sheet_runner.process_pdf')
    @patch('sheet_runner._load_history')
    @patch('sheet_runner._add_to_history')
    @patch('os.path.exists')
    @patch.dict(os.environ, {'SPREADSHEET_ID': 'mock_id'})
    def test_main_flow(self, mock_path_exists, mock_add_history, mock_load_history, mock_process_pdf, mock_get_data):
        """Test the main execution flow of sheet_runner."""
        # Setup mocks
        mock_get_data.return_value = [
            {
                'atomizar libro': 'SI',
                'url local': 'test_book.pdf',
                'título original del libro': 'Test Book',
                'autor (nombre apellido)': 'Test Author',
                'año de publicación': '2023',
                'indice': 'Chapter 1',
                'generar resumen': 'NO'
            }
        ]
        mock_load_history.return_value = set()
        mock_path_exists.return_value = True # Pretend PDF exists

        # Execute
        runner_main()

        # Verify process_pdf was called correctly
        mock_process_pdf.assert_called_once()
        call_args = mock_process_pdf.call_args[1]
        self.assertEqual(call_args['title'], 'Test Book')
        self.assertEqual(call_args['author'], 'Test Author')
        self.assertEqual(len(call_args['toc_from_csv']), 1)
        self.assertEqual(call_args['generate_summaries'], False) # Check if 'NO' converted to False

        # Verify history was updated
        mock_add_history.assert_called_once_with('test_book.pdf')

if __name__ == '__main__':
    unittest.main()
