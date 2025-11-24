import logging
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from pdf_atomic_pro.core import batch
from pdf_atomic_pro.core.utils.logging_utils import setup_logging
from pdf_atomic_pro.core.utils.config_loader import load_config

# Setup Logging
setup_logging(log_level=load_config().get('log_level', 'INFO'))
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Atomic Pro API")

# Configuration for Static Files
BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIST_DIR = BASE_DIR / "ui" / "dist"

# Ensure UI directory exists
if not UI_DIST_DIR.exists():
    os.makedirs(UI_DIST_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(UI_DIST_DIR)), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend is running."""
    return {"status": "ok", "app": "PDF Atomic Pro"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the minimal UI."""
    index_path = UI_DIST_DIR / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PDF Atomic Pro - UI Not Found</h1>"

@app.post("/api/batch/process")
async def trigger_batch_process(background_tasks: BackgroundTasks):
    """Triggers the batch processing of PDFs from the CSV."""

    def _run_batch():
        logger.info("Starting batch process triggered by API...")
        try:
            # Call the core batch logic
            # Assuming batch.process_batch exists and handles the logic
            # We pass defaults or read from config/env
            batch.process_batch(no_ai=False, translate_to=None)
            logger.info("Batch process completed.")
        except Exception as e:
            logger.error(f"Error during batch process: {e}", exc_info=True)

    background_tasks.add_task(_run_batch)
    return {"message": "Batch processing started in background."}

# --- Stub Endpoints (Future Use) ---

@app.post("/api/process_pdf")
async def process_pdf_stub():
    """Stub for processing a single PDF."""
    return {"status": "not_implemented"}

@app.get("/api/preview_toc")
async def preview_toc_stub():
    """Stub for previewing TOC."""
    return {"status": "not_implemented"}
