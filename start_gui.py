import uvicorn
import webbrowser
import threading
import time
import sys
import socket
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DEFAULT_PORT = 8080
HOST = "127.0.0.1"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        print(f"[INFO] Puerto {port} ocupado, probando el siguiente...")
        port += 1
        if port > start_port + 10: # Don't search forever
            raise Exception("No se encontraron puertos disponibles en el rango cercano.")
    return port

def wait_for_server(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False

def start_server(port):
    """Starts the Uvicorn server."""
    # Force 127.0.0.1 for local usage only
    uvicorn.run("web_plugin.main:app", host=HOST, port=port, log_level="warning")

def main():
    print("="*50)
    print("   🚀 PDF Atomic Pro - Panel de Control Local")
    print("="*50)

    try:
        port = find_available_port(DEFAULT_PORT)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    url = f"http://{HOST}:{port}"
    print(f"[INIT] Iniciando servidor local en {url} ...")

    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if wait_for_server(port):
        print(f"[LISTO] Servidor activo.")
        print(f"[AUTO] Abriendo navegador en: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[WARN] No se pudo abrir el navegador automáticamente: {e}")
            print(f"👉 Por favor, abre manualmente este link: {url}")
    else:
        print("[ERROR] El servidor tardó demasiado en iniciar.")
        sys.exit(1)

    print("\n✅ El programa está corriendo. Mantén esta ventana abierta.")
    print("❌ Presiona Ctrl+C para detenerlo y salir.")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SALIR] Cerrando aplicación...")
        sys.exit(0)

if __name__ == "__main__":
    main()
