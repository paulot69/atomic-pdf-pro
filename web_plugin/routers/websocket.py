from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from web_plugin.routers.api import log_manager

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await log_manager.connect(websocket)
    try:
        while True:
            # Keep connection open, wait for messages if client sends any (heartbeat?)
            # Currently we only push from server.
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_manager.disconnect(websocket)
