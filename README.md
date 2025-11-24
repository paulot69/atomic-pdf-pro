# 🌲 **PDF Atomic Pro — Roadmap Profesional**

Objetivo:
Convertir lo que hoy es un proyecto poderoso pero “artesanal” en **una aplicación local profesional, estable, robusta, con interfaz completa y ejecutable**, sin depender de servidores externos ni infraestructura pagada.

# 🚀 Guía de Instalación y Uso

### 📋 Requisitos Previos

1.  **Docker Desktop** (para Windows/macOS) o **Docker Engine** (para Linux).
2.  (Opcional) Python 3.11+ instalado localmente para ejecución sin Docker.

### 🐳 Ejecución con Docker (Modo Profesional)

PDF Atomic Pro puede ejecutarse completamente dentro de un contenedor Docker, incluyendo OCR, FastAPI y la interfaz web local. No necesitas instalar Python, Tesseract o Poppler en tu sistema.

**Paso 1 — Construir la imagen de Docker**

Desde la raíz del proyecto, abre tu terminal y ejecuta:

```bash
docker build -t atomic-pdf-pro .
```

**Paso 2 — Preparar carpetas locales**

Asegúrate de tener definidas tus carpetas de entrada (donde están tus PDFs) y salida (donde quieres los vaults).

**Paso 3 — Iniciar la Aplicación Web**

Ejecuta el siguiente comando (ajusta las rutas a tu sistema):

```bash
docker run --rm -p 8080:8080 \
  -v "G:\Mi unidad\06_BIBLIOTECA_DIGITAL:/input" \
  -v "D:\LibrosAtomicosOutput:/output" \
  atomic-pdf-pro
```

Una vez ejecutado, **abre tu navegador web y ve a: `http://127.0.0.1:8080`**

### 💻 Ejecución Local (Sin Docker)

1.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
2.  Configura tu entorno copiando el ejemplo:
    ```bash
    cp llaves/.env.example llaves/.env
    ```
    *(Edita `llaves/.env` y ajusta `LOCAL_INPUT_PATH` a la ruta raíz de tus PDFs)*
3.  Ejecuta la aplicación:
    ```bash
    python start_gui.py
    ```

---

# ⚙️ Configuración

La configuración se maneja a través de variables de entorno y el archivo `config/settings.json`. El sistema carga la configuración en el siguiente orden de prioridad:
1.  Variables de entorno (incluyendo `llaves/.env`).
2.  `config/settings.json`.

### Variables Clave (.env)

*   `DOCKERIZED`: `true` para Docker, `false` para local.
*   `LOCAL_INPUT_PATH`: Ruta raíz local donde buscar PDFs recursivamente (ej. `G:/Biblioteca`).
*   `LOCAL_OUTPUT_PATH`: Ruta local donde guardar los vaults generados.
*   `DOCKER_INPUT_PATH_PREFIX`: Ruta interna en Docker para entrada (default `/input`).
*   `DOCKER_OUTPUT_PATH`: Ruta interna en Docker para salida (default `/output`).
*   `SHEET_ID_ATOMICO`: ID del Google Sheet de control.

---

# 📂 Estructura del Proyecto (V1)

```
atomic-pdf-pro/
│
├── pdf_atomic_pro/                 ← Paquete principal
│   │
│   ├── core/                       ← Lógica de negocio
│   │   ├── extractor/              ← Extracción de texto/OCR
│   │   ├── estructura/             ← Detección de índice y capítulos
│   │   ├── generacion/             ← Generación de notas y MOCs
│   │   ├── integridad/             ← Verificación de enlaces
│   │   ├── limpieza/               ← Normalización de texto
│   │   ├── traduccion/             ← Módulo de traducción
│   │   ├── utils/                  ← Utilidades del Core
│   │   │   ├── paths.py            ← Búsqueda recursiva
│   │   │   ├── config_loader.py    ← Carga unificada de configuración
│   │   │   └── logging_utils.py    ← Setup de logs
│   │   └── pipeline.py             ← Orquestador principal
│   │
│   ├── api/                        ← API FastAPI
│   │   ├── server.py               ← Endpoints y servidor
│   │   └── models.py               ← Modelos Pydantic
│   │
│   ├── ui/                         ← Frontend estático
│   │   └── dist/
│   │
│   └── __init__.py
│
├── config/                         ← Configuración de usuario
│   ├── settings.json
│   ├── taxonomy_rules.txt
│   └── templates/                  ← Plantillas YAML
│
├── logs/                           ← Logs de la aplicación
│   └── app.log
│
├── llaves/                         ← Credenciales y secretos (Gitignored)
│   ├── .env
│   └── .env.example
│
├── Dockerfile                      ← Definición de imagen Docker
├── requirements.txt
├── start_gui.py                    ← Launcher
└── README.md
    ```

---

# 📝 Flujo de Trabajo

1.  **Google Sheet**: Añade tus libros al Sheet de control. En la columna 'url local', coloca **SOLO el nombre del archivo** (ej. `El Hobbit.pdf`).
2.  **Carga**: La aplicación buscará ese archivo recursivamente en tu biblioteca (`/input` o `LOCAL_INPUT_PATH`) sin importar en qué subcarpeta esté.
3.  **Procesamiento**: El pipeline extrae texto, detecta estructura, genera notas atómicas y crea el vault Obsidian.
4.  **Salida**: El resultado aparece en tu carpeta de salida configurada.

---

# 🧪 Pruebas

Para asegurar la estabilidad y el correcto funcionamiento del proyecto, se ha integrado un sistema de pruebas automatizadas utilizando `pytest`.

### 🛠️ Instalación de Dependencias de Pruebas

Asegúrate de tener instaladas las dependencias necesarias para las pruebas:

```bash
pip install -r requirements.txt
```
*(Esto instalará `pytest`, `pytest-cov` para cobertura de código y `pytest-mock` para simular partes del sistema.)*

### ▶️ Ejecutar Pruebas

Para ejecutar todas las pruebas y generar un informe de cobertura de código, abre tu terminal en la raíz del proyecto y ejecuta:

```bash
pytest
```

### 🔬 La Primera Prueba: `test_process_pdf_full_pipeline`

Esta prueba, ubicada en `tests/test_pipeline.py`, es una prueba de "extremo a extremo" (end-to-end) del pipeline principal de procesamiento de PDFs. Su objetivo es verificar que todo el flujo central de `pdf_atomic_pro` funciona correctamente:

*   **Simulación de Extracción de Texto:** Utiliza `pytest-mock` para simular la extracción de texto de un PDF. Esto permite que la prueba se ejecute de forma rápida y determinista, sin depender de un archivo PDF real ni de los motores de extracción.
*   **Generación de Estructura:** Verifica que el proceso de estructuración (detección de capítulos, generación de notas atómicas y Mapas de Contenido o MOCs) se realice de forma adecuada.
*   **Verificación de Salida:** Comprueba que la carpeta del vault de Obsidian se crea correctamente en un directorio temporal y que contiene los archivos esperados (MOCs principales, carpetas de capítulos y notas atómicas).

**Nota sobre `tests/assets/sample.pdf`:** Para que las pruebas sean completamente representativas del proceso de extracción real, se recomienda reemplazar el archivo `tests/assets/sample.pdf` (inicialmente vacío) por un PDF pequeño pero real (por ejemplo, de 1-2 páginas). Esto permitirá que las pruebas también validen la etapa inicial de extracción de texto/OCR.

