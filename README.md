# PDF Atomic Pro: Edición Inteligente

## Descripción

**PDF Atomic Pro** transforma archivos PDF en **Vaults de Obsidian** estructurados, navegables y enriquecidos con metadatos inteligentes. La herramienta prioriza la estructura del índice del autor para crear un conjunto de notas atómicas limpias e interconectadas.

## Características Principales

-   **Detección de Índice Experta:** Utiliza un sistema de tres capas (bookmarks, búsqueda textual, análisis estructural) para replicar fielmente la jerarquía del libro.
-   **Normalización del Contenido:** Limpia y reconstruye el texto para máxima legibilidad sin alterar la redacción original.
-   **Sistema de Tags Híbrido:**
    -   **Estructurales (Automáticos):** `libro/titulo`, `capitulo/nombre` para organización.
    -   **Semánticos (IA):** Generados por IA para facilitar el descubrimiento de temas, con reglas personalizables.
-   **Auditoría de Tags:** Genera un reporte con todos los tags únicos utilizados en un libro, ideal para supervisar la IA.
-   **Navegación Fluida:** Crea Mapas de Contenido (MOCs) y pies de página con `dataviewjs` para una exploración intuitiva.
-   **Automatización con Google Sheets:** Permite gestionar una cola de libros y configuraciones desde una hoja de cálculo, utilizando una cuenta de servicio segura.

## Estructura del Proyecto

```
pdf-atomic-pro/
├── llaves/                # Credenciales de API (IGNORADO por git)
├── Libros Atomicos/       # Salida por defecto de los vaults generados (IGNORADO por git)
├── config/                # Reglas de taxonomía y configuración (IGNORADO por git)
├── pdf_atomic_pro/        # Código fuente principal
├── tests/                 # Tests unitarios
├── sheet_runner.py        # Script orquestador para procesamiento por lotes
├── main.py                # Script de procesamiento individual
└── ...
```

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu_usuario/pdf-atomic-pro.git
    cd pdf-atomic-pro
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

Antes de usar el programa, es necesario configurar el entorno.

1.  **Crear el archivo `.env`:**
    *   Crea una copia del archivo `.env.example` y renómbrala a `.env`.
    *   **SPREADSHEET_ID**: (Obligatorio para Modo 2) El ID de tu hoja de cálculo de Google. Lo encuentras en la URL: `https://docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit`.

2.  **Configurar la IA (Opcional):**
    *   Abre tu archivo `.env`.
    *   Añade tu clave de API de Google Gemini a la variable `GEMINI_API_KEY`.
    *   Si dejas esta clave vacía, el programa funcionará en modo local (sin IA).

3.  **Configurar Google Service Account (Obligatorio para Modo 2):**
    *   Crea una Service Account en Google Cloud Console.
    *   Descarga el archivo JSON de la clave.
    *   Renombra el archivo a `torre_credentials.json`.
    *   Coloca el archivo en la carpeta `llaves/`.
    *   **Importante:** Comparte tu hoja de Google Sheets (editor) con el correo electrónico de la Service Account (que aparece en el JSON `client_email`).

4.  **Personalizar la Taxonomía de la IA (Avanzado):**
    *   Puedes editar las reglas que sigue la IA para generar tags modificando el archivo: `config/taxonomy_rules.txt` (si existe).

## Uso

El programa tiene dos modos de ejecución. Para el flujo de trabajo principal y automatizado, solo necesitas usar el **Modo 2**.

### Modo 1: Procesar un Solo PDF (Manual)

Este modo es útil para procesar un único archivo de forma rápida y aislada. Se utiliza el script `main.py`.

**Sintaxis:**
```bash
python main.py <ruta_al_pdf> [argumentos_opcionales]
```

### Modo 2: Procesar en Lote desde Google Sheets (Automático)

Este es el modo recomendado. Utiliza `sheet_runner.py` para leer tu hoja de cálculo, autenticándose de forma segura con la Service Account.

**Sintaxis:**
```bash
# Procesar todos los libros nuevos marcados en la hoja
python sheet_runner.py

# Procesar todos los libros nuevos sin usar la IA
python sheet_runner.py --sin-ia
```

<<<<<<< HEAD
**Requisitos de la Hoja de Cálculo:**
La hoja debe tener las siguientes columnas (el script normaliza los nombres, así que mayúsculas/minúsculas no importan):
=======
### Modo 3: Panel Web / Local (Interfaz Gráfica)

Esta es la forma recomendada y más visual de utilizar la herramienta. Proporciona un panel de control (similar a una app de escritorio) donde puedes seleccionar libros, configurar opciones avanzadas y ver el progreso en tiempo real.

**Cómo iniciarlo:**
```bash
python start_gui.py
```

Este comando iniciará el servidor y **abrirá automáticamente tu navegador** con el panel de control listo para usar.

**Funcionalidades del Panel:**
-   **Modo Un Solo Libro:** Selecciona un libro de tu lista, pega la estructura del índice manualmente si lo deseas, y procésalo al instante.
-   **Modo Lote (Batch):** Procesa automáticamente todos los libros marcados con "SI" en la hoja de cálculo.
-   **Consola en Tiempo Real:** Visualiza los logs de ejecución directamente en la web.
-   **Configuración Avanzada:** Activa/desactiva la IA o la traducción con simples interruptores.

**Requisitos de la Hoja:**
Tu hoja de cálculo debe contener, como mínimo, las siguientes columnas:
-   `ATOMIZAR LIBRO.` (con el valor "SI" para los libros a procesar).
-   `URL LOCAL` (con la ruta completa al archivo PDF).
-   `Título Original del Libro`
-   `Autor (Nombre Apellido)`
-   `Año de Publicación`
>>>>>>> origin/web-plugin-dashboard

| Columna | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `ATOMIZAR LIBRO` | Escribe "SI" para procesar. | `SI` |
| `URL LOCAL` | Ruta absoluta al archivo PDF. | `C:\Libros\Clean Code.pdf` |
| `Título Original del Libro` | Título para los metadatos. | `Clean Code` |
| `Autor (Nombre Apellido)` | Autor del libro. | `Robert C. Martin` |
| `Año de Publicación` | Año de publicación. | `2008` |
| `INDICE` | (Opcional) Estructura jerárquica identada (4 espacios). | Ver abajo |
| `CARPETA TEMÁTICA FINAL` | (Opcional) Carpeta raíz temática. | `Ingeniería de Software` |
| `TEMA (PARA NOMENCLATURA)` | (Opcional) Prefijo para tags. | `dev` |
| `GENERAR RESUMEN` | Escribe "SI" para activar resúmenes con IA. | `SI` |

**Ejemplo de Índice Personalizado (Columna INDICE):**
```text
Parte 1: Principios
    Capítulo 1: Código Limpio
Parte 2: Práctica
    Capítulo 2: Nombres con Sentido
```

## Salida

Los vaults generados se guardarán por defecto en la carpeta `Libros Atomicos/` dentro del directorio del proyecto.

```
Libros Atomicos/
└── [Año] - [Título del Libro] - [Autor]/
    ├── MOC - [Título del Libro].md
    ├── Capítulo 01 - [Título del Capítulo]/
    │   ├── MOC - [Título del Capítulo].md
    │   ├── 1.1 - [Concepto Atómico 1].md
    │   └── ...
    └── ...
```

## Solución de Problemas (Troubleshooting)

- **Error: "Spreadsheet not found"**: Verifica que el `SPREADSHEET_ID` en `.env` sea correcto y que hayas compartido la hoja con el email de la Service Account.
- **Error de Credenciales**: Asegúrate de que `llaves/torre_credentials.json` existe y es un JSON válido.
- **ImportError**: Ejecuta `pip install -r requirements.txt` para asegurar que tienes todas las librerías nuevas (`google-api-python-client`, etc.).
