import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SheetManager:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.credentials_path = 'credentials.json'
        self.client = None
        self.sheet = None
        self.sheet_url = os.getenv("SHEET_CSV_URL")  # Note: This is usually a published CSV URL in .env, but we need the real sheet for editing
        # For writing, we typically need the Sheet ID or Name if we are using Service Account
        # Ideally, the .env should also have a SHEET_NAME or SHEET_ID if we are not using the URL to open it.
        # But gspread can open by URL if authorized.

        # Columns configuration (0-based index for internal logic, but gspread uses 1-based or names)
        # Based on requirements:
        # Col H (Index 7): Title of File FINAL (.pdf)
        # Col L (Index 11): INDICE
        # Col A (Index 0): ATOMIZAR LIBRO.
        # Col URL LOCAL (Usually checking header, but let's assume mapped from `sheet_runner.py` logic)

        self._connect()

    def _connect(self):
        if not os.path.exists(self.credentials_path):
            logger.warning("credentials.json not found. Running in Mock Mode.")
            self.client = None
            return

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, self.scope)
            self.client = gspread.authorize(creds)

            # Attempt to open the sheet
            # We need the actual Google Sheet URL (edit mode), not the CSV export URL.
            # If SHEET_CSV_URL is a published CSV, we can't use it to edit.
            # We will assume for now there is an environment variable for the editable Sheet or we try to use the one provided
            # If it fails, we fallback to mock.

            # For the purpose of this task, if we can't open it, we Mock.
            # Let's assume we need a SHEET_NAME or SHEET_KEY
            sheet_name = os.getenv("SHEET_NAME", "Atomic PDF Control") # Fallback name

            try:
                self.sheet = self.client.open(sheet_name).sheet1
            except Exception:
                # Try opening by URL if it looks like a real sheet URL
                if self.sheet_url and "docs.google.com" in self.sheet_url and "/pub" not in self.sheet_url:
                     self.sheet = self.client.open_by_url(self.sheet_url).sheet1
                else:
                    logger.error("Could not open sheet. Check SHEET_NAME or SHEET_CSV_URL.")
                    self.client = None # Fallback to mock

        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.client = None

    def get_all_books(self) -> List[Dict]:
        """
        Returns a list of books with their metadata.
        If connection fails, returns dummy data.
        """
        if not self.client or not self.sheet:
            return self._get_mock_books()

        try:
            records = self.sheet.get_all_records()
            books = []
            # We need to map the records to a standard format and keep track of Row Index (1-based)
            # get_all_records returns a list of dicts. Row 2 in Sheet is index 0 in list.
            # So Row Index = list_index + 2

            for idx, row in enumerate(records):
                books.append({
                    "row_index": idx + 2,
                    "title": row.get("Título Original del Libro", ""),
                    "filename": row.get("Título de Archivo FINAL (.pdf)", ""),
                    "local_path": row.get("URL LOCAL", ""),
                    "author": row.get("Autor (Nombre Apellido)", ""),
                    "year": row.get("Año de Publicación", ""),
                    "status": row.get("ATOMIZAR LIBRO.", ""),
                    "index_structure": row.get("INDICE", "")
                })
            return books
        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            return self._get_mock_books()

    def update_book_status(self, row_index: int, status: str = "SI", clear_others: bool = True):
        """
        Updates the status of a specific book.
        If clear_others is True, sets "ATOMIZAR LIBRO." to empty/NO for all other rows.
        """
        if not self.client or not self.sheet:
            logger.info(f"[MOCK] Update Book Status: Row {row_index} -> {status}, Clear Others: {clear_others}")
            return

        try:
            # Find the column index for "ATOMIZAR LIBRO."
            # We can cache this, but for safety we find it every time or hardcode if confident.
            # Using find is safer.
            cell = self.sheet.find("ATOMIZAR LIBRO.")
            col_idx = cell.col

            if clear_others:
                # Get all values in that column
                col_values = self.sheet.col_values(col_idx)
                # Prepare batch update list
                # We only want to change values that are "SI" to ""
                # and the target row to "SI"

                updates = []
                for i in range(len(col_values)): # 0-based list, matches row i+1
                    current_row = i + 1
                    if current_row == 1: continue # Skip header

                    if current_row == row_index:
                        updates.append({"range": gspread.utils.rowcol_to_a1(current_row, col_idx), "values": [[status]]})
                    else:
                        # If it was SI, clear it. Or just strictly clear everything else?
                        # Requirements: "TODAS LAS CELDAS DE la linea L deben estar vacias" (Wait, Line L is INDICE)
                        # "y la unica que debe decir SI es la del libro seleccionado" (Refering to ATOMIZAR LIBRO probably)
                        # Let's assume we clear the ATOMIZAR LIBRO column for others.
                        if col_values[i].strip().upper() == "SI":
                             updates.append({"range": gspread.utils.rowcol_to_a1(current_row, col_idx), "values": [[""]]})

                if updates:
                    self.sheet.batch_update(updates)
            else:
                # Just update the specific row
                self.sheet.update_cell(row_index, col_idx, status)

        except Exception as e:
            logger.error(f"Error updating book status: {e}")

    def update_book_structure(self, row_index: int, structure_text: str):
        """
        Updates the Index (Col L) for a specific book.
        And clears Col L for all other books if implied by requirements.
        Req: "TODAS LAS CELDAS DE la linea L deben estar vacias y la unica que debe decir SI es la del libro seleccionado"
        Wait, user said "TODAS LAS CELDAS DE la linea L deben estar vacias".
        If L is INDICE, maybe they meant:
        1. Only the selected book has the INDICE text.
        2. Only the selected book has "SI" in ATOMIZAR LIBRO.

        Let's assume we clear INDICE for others too to be safe, or at least ensuring we write the structure to the target.
        """
        if not self.client or not self.sheet:
            logger.info(f"[MOCK] Update Book Structure: Row {row_index} -> Length {len(structure_text)}")
            return

        try:
            cell = self.sheet.find("INDICE")
            col_idx = cell.col

            # Clear others? "TODAS LAS CELDAS DE la linea L deben estar vacias"
            # Yes, it implies exclusivity for the Index too in this mode.

            col_values = self.sheet.col_values(col_idx)
            updates = []

            for i in range(len(col_values)):
                current_row = i + 1
                if current_row == 1: continue

                if current_row == row_index:
                    updates.append({"range": gspread.utils.rowcol_to_a1(current_row, col_idx), "values": [[structure_text]]})
                else:
                    if col_values[i]: # If not empty
                        updates.append({"range": gspread.utils.rowcol_to_a1(current_row, col_idx), "values": [[""]]})

            if updates:
                self.sheet.batch_update(updates)

        except Exception as e:
            logger.error(f"Error updating book structure: {e}")

    def _get_mock_books(self):
        return [
            {
                "row_index": 2,
                "title": "El Quijote",
                "filename": "quijote.pdf",
                "local_path": "/tmp/quijote.pdf",
                "author": "Cervantes",
                "year": "1605",
                "status": "SI",
                "index_structure": ""
            },
            {
                "row_index": 3,
                "title": "Cien Años de Soledad",
                "filename": "cien_anos.pdf",
                "local_path": "/tmp/cien_anos.pdf",
                "author": "Gabo",
                "year": "1967",
                "status": "",
                "index_structure": ""
            }
        ]
