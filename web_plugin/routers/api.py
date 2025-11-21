from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from web_plugin.services.sheet_service import SheetManager
from web_plugin.services.runner_service import RunnerService
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
sheet_manager = SheetManager()
runner_service = RunnerService()

# Shared state for logs
class LogManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

log_manager = LogManager()

# --- Models ---
class SingleProcessRequest(BaseModel):
    row_index: int
    structure_content: Optional[str] = ""
    no_ai: Optional[bool] = False
    translate_to: Optional[str] = ""

class BatchProcessRequest(BaseModel):
    no_ai: Optional[bool] = False
    translate_to: Optional[str] = ""

# --- Routes ---

@router.get("/api/books")
def get_books():
    books = sheet_manager.get_all_books()
    return {"books": books}

@router.post("/api/process/single")
async def process_single(req: SingleProcessRequest, background_tasks: BackgroundTasks):
    """
    1. Updates Sheet (Exclusive SI + Structure).
    2. Starts background task to run script.
    """
    books = sheet_manager.get_all_books()
    book = next((b for b in books if b["row_index"] == req.row_index), None)

    if not book:
        return JSONResponse(content={"error": "Libro no encontrado"}, status_code=404)

    # Update Sheet
    sheet_manager.update_book_status(req.row_index, "SI", clear_others=True)

    if req.structure_content:
        sheet_manager.update_book_structure(req.row_index, req.structure_content)

    # Trigger Execution
    background_tasks.add_task(
        _run_and_stream_single,
        book["local_path"],
        book["title"],
        book["author"],
        book["year"],
        req.structure_content,
        req.no_ai,
        req.translate_to
    )

    return {"status": "started", "message": f"Procesando '{book['title']}'"}

@router.post("/api/process/batch")
async def process_batch(req: BatchProcessRequest, background_tasks: BackgroundTasks):
    """
    1. Reads all books marked as SI.
    2. Starts background task for batch.
    """
    books = sheet_manager.get_all_books()
    target_books = [b for b in books if str(b.get("status", "")).strip().upper() == "SI"]

    if not target_books:
         return JSONResponse(content={"error": "No hay libros marcados con 'SI'"}, status_code=400)

    # Trigger Execution
    background_tasks.add_task(_run_and_stream_batch, target_books, req.no_ai, req.translate_to)

    return {"status": "started", "message": f"Iniciando lote de {len(target_books)} libros"}

# --- Internal Task Wrappers ---
async def _run_and_stream_single(filepath, title, author, year, structure, no_ai, translate_to):
    async for line in runner_service.run_single(filepath, title, author, year, structure, no_ai, translate_to):
        await log_manager.broadcast(line)

async def _run_and_stream_batch(books, no_ai, translate_to):
    async for line in runner_service.run_batch(books, no_ai, translate_to):
        await log_manager.broadcast(line)
