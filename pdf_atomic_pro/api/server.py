import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
from pathlib import Path

from pdf_atomic_pro.api.models import ProcessRequest, BatchProcessRequest, BookListResponse, Book
from pdf_atomic_pro.core import batch, pipeline
from pdf_atomic_pro.core.utils import find_pdf_recursive # NEW IMPORT

# Setup API
app = FastAPI(title="PDF Atomic Pro API")

# Directories
# En Docker, el directorio de trabajo es /app. La estructura del proyecto es plana dentro de /app.
# UI_DIR está en /app/pdf_atomic_pro/ui/dist. STATIC_DIR está en /app/pdf_atomic_pro/ui/dist/static.
# BASE_DIR para el paquete pdf_atomic_pro es /app/pdf_atomic_pro.

UI_DIR = Path(os.getenv("UI_DIR", "/app/pdf_atomic_pro/ui/dist")) # Modificación 2. Reemplazar UI_DIR
STATIC_DIR = UI_DIR / "static" # Modificación 2. Reemplazar STATIC_DIR
BASE_DIR = Path(__file__).resolve().parent.parent # Sigue siendo útil para referencias internas del paquete

# Configuración para rutas de PDF y salida (específico de Docker, configurable vía variables de entorno)
DOCKER_INPUT_PATH_PREFIX = os.getenv("DOCKER_INPUT_PATH_PREFIX", "/input") # Por ejemplo, "/input"
DOCKER_OUTPUT_PATH = os.getenv("DOCKER_OUTPUT_PATH", "./Libros Atomicos") # Ruta de salida predeterminada local

# Ensure static dir exists
if not STATIC_DIR.exists():
    os.makedirs(STATIC_DIR)

# Mount Static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(UI_DIR))

# --- WebSocket Logger ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Override standard logger to broadcast to WS
class WebSocketHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # Run async send in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.broadcast(log_entry + "\n"))
        except:
            pass # Can't log if loop is closed

ws_handler = WebSocketHandler()
ws_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] > %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(ws_handler)
logging.getLogger().setLevel(logging.INFO)


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/books", response_model=BookListResponse)
async def get_books():
    try:
        data = batch.get_sheet_data()
        books = []
        for item in data:
            books.append(Book(
                row_index=item.get('row_index'),
                title=item.get('título original del libro', 'Sin Título'),
                filename=os.path.basename(item.get('url local', '').replace('"', '')),
                status="Ready"
            ))
        return {"books": books}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/process/single")
async def process_single(req: ProcessRequest, background_tasks: BackgroundTasks):

    def _task():
        try:
            logging.info(f"Iniciando tarea individual para ID {req.row_index}...")
            # Fetch fresh data
            data = batch.get_sheet_data()
            book_data = next((b for b in data if b['row_index'] == req.row_index), None)

            if not book_data:
                logging.error("Libro no encontrado.")
                return

            # Sustituir la lógica actual del pdf_path por:
            raw_pdf_name = book_data.get('url local', '').strip()

            pdf_path = None
            if os.getenv("DOCKERIZED") == "true":
                pdf_path = find_pdf_recursive(
                    raw_pdf_name,
                    os.getenv("DOCKER_INPUT_PATH_PREFIX", "/input")
                )
            else:
                pdf_path = raw_pdf_name # uso local
            
            # Validación
            if pdf_path is None:
                raise FileNotFoundError(f"PDF no encontrado en la carpeta /input o en ruta local: {raw_pdf_name}")

            # Use provided structure if any, else from sheet
            toc_entries = []
            if req.structure_content:
                toc_entries = batch.parse_toc_from_string(req.structure_content)
            else:
                toc_entries = batch.parse_toc_from_string(book_data.get('indice', ''))

            # Progress Wrapper
            def progress_report(pct, msg):
                logging.info(f"[{pct}%] {msg}")

            pipeline.process_pdf(
                pdf_path=pdf_path,
                title=book_data.get('título original del libro', ''),
                author=book_data.get('autor (nombre apellido)', ''),
                year=book_data.get('año de publicación', ''),
                output_dir=os.getenv("DOCKER_OUTPUT_PATH", "./Libros Atomicos"), # Reemplazar la definición de output_dir
                toc_from_csv=toc_entries,
                thematic_folder=book_data.get('carpeta temática final', ''),
                theme_nomenclature=book_data.get('tema (para nomenclatura)', ''),
                use_ai=not req.no_ai,
                generate_summaries=book_data.get('generar resumen', 'SI').upper() == 'SI',
                translate_to=req.translate_to,
                progress_callback=progress_report
            )

        except Exception as e:
            logging.error(f"Error en tarea: {e}")

    background_tasks.add_task(_task)
    return {"message": "Procesamiento iniciado en segundo plano."}

@app.post("/api/process/batch")
async def process_batch_endpoint(req: BatchProcessRequest, background_tasks: BackgroundTasks):

    def _task():
        logging.info("Iniciando modo batch...")
        try:
            count = batch.process_batch(
                no_ai=req.no_ai,
                translate_to=req.translate_to,
                update_progress_func=lambda i, t, m: logging.info(f"BATCH ({i}/{t}): {m}")
            )
            logging.info(f"Batch finalizado. {count} libros procesados.")
        except Exception as e:
            logging.error(f"Error crítico en batch: {e}")

    background_tasks.add_task(_task)
    return {"message": "Procesamiento por lotes iniciado."}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
