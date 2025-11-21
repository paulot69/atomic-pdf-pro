from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from web_plugin.routers import api, websocket
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="PDF Atomic Pro - Web Plugin")

# Mount static files
app.mount("/static", StaticFiles(directory="web_plugin/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web_plugin/templates")

# Mount routers
app.include_router(api.router)
app.include_router(websocket.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ui", response_class=HTMLResponse)
async def ui_redirect(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    # Port updated to 8080 as requested
    uvicorn.run("web_plugin.main:app", host="0.0.0.0", port=8080, reload=True)
