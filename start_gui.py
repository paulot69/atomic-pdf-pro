import uvicorn
import webbrowser
import threading
import time
import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

HOST = "0.0.0.0"
PORT = 8080
URL = f"http://localhost:{PORT}"

def start_server():
    """Starts the Uvicorn server."""
    # We use the string import to enable reload if needed, but for a GUI launcher,
    # direct invocation or app instance is often cleaner.
    # However, uvicorn.run with string is standard.
    # We turn off reload for the production-like launcher to avoid reloading loops if not needed,
    # but user might want it. Let's keep it simple.
    uvicorn.run("web_plugin.main:app", host=HOST, port=PORT, log_level="info")

def main():
    print("="*50)
    print("   🚀 PDF Atomic Pro - Panel de Control Local")
    print("="*50)
    print(f"Iniciando servidor en puerto {PORT}...")

    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait a bit for the server to warm up
    time.sleep(2)

    print(f"Abrir navegador en: {URL}")
    try:
        webbrowser.open(URL)
    except Exception as e:
        print(f"No se pudo abrir el navegador automáticamente: {e}")
        print(f"Por favor, abre {URL} manualmente.")

    print("\n[INFO] El programa se está ejecutando. Presiona Ctrl+C para salir.")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCerrando aplicación...")
        sys.exit(0)

if __name__ == "__main__":
    main()
