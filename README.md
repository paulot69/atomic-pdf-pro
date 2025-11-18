# PDF Atomic Pro

## Descripción

**PDF Atomic Pro** es una herramienta de línea de comandos diseñada para transformar archivos PDF en un **Vault de Obsidian estructurado y "atómico"**. Va más allá de la simple extracción de texto, aplicando un proceso de destilación de contenido para crear notas atómicas interconectadas, enriquecidas con metadatos YAML y un sistema de navegación robusto, siguiendo la filosofía de "Libros Atómicos" para la gestión del conocimiento.

El proceso incluye:
1.  **Extracción de Texto Inteligente:** Extrae texto de PDFs, con un sistema de fallback a OCR para documentos escaneados, y limpieza de encabezados/pies de página.
2.  **Estructuración Atómica:** Divide el contenido en capítulos y secciones, y luego en notas atómicas individuales, cada una centrada en una idea clave.
3.  **Enriquecimiento de Metadatos:** Genera `YAML frontmatter` estandarizado para cada nota atómica, incluyendo tags, resúmenes y alias, facilitando la organización y búsqueda en Obsidian.
4.  **Navegación Integrada:** Crea `wikilinks` automáticos entre notas relacionadas y añade un pie de página de navegación con scripts `dataviewjs` para una exploración fluida.
5.  **Mapas de Contenido (MOCs):** Genera MOCs a nivel de capítulo y un MOC principal para el libro completo, proporcionando una vista jerárquica y enlaces a todas las notas.
6.  **Verificación de Integridad:** Audita todos los enlaces internos para asegurar que no haya enlaces rotos en el vault generado.

## Instalación

Para usar PDF Atomic Pro, primero necesitas clonar el repositorio e instalar las dependencias de Python.

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu_usuario/pdf-atomic-pro.git
    cd pdf-atomic-pro
    ```
    *(Nota: Si ya tienes el repositorio, omite este paso.)*

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Uso

El programa se ejecuta desde la línea de comandos. Necesitas especificar el directorio de entrada con tus archivos PDF, un directorio de salida para el vault pre-atómico (aunque la salida principal será el vault atómico), y metadatos del libro como título, autor y año.

**Sintaxis:**
```bash
python main.py <input_dir> <output_dir_preatomic> --titulo "<Título del Libro>" --autor "<Autor del Libro>" --ano "<Año>" [--atomic_output_dir "<Directorio de Salida Atómico>"]
```

**Argumentos:**
*   `<input_dir>`: Ruta al directorio que contiene el/los archivo(s) PDF a procesar.
*   `<output_dir_preatomic>`: Ruta al directorio donde se guardará la estructura pre-atómica (salida intermedia).
*   `--titulo`: El título completo del libro. **Obligatorio.**
*   `--autor`: El autor del libro. **Obligatorio.**
*   `--ano`: El año de publicación del libro. **Obligatorio.**
*   `--atomic_output_dir`: (Opcional) Ruta al directorio raíz donde se creará el vault atómico final. Por defecto es `D:\github\Libros Atomicos`.

**Ejemplo:**
Asegúrate de tener un archivo PDF (por ejemplo, `mi_libro.pdf`) dentro de `D:\github\pdf-atomic-pro\input`.

```bash
python D:\github\pdf-atomic-pro\main.py "D:\github\pdf-atomic-pro\input" "D:\github\pdf-atomic-pro\output_preatomic" --titulo "Ejemplo de Libro" --autor "Autor de Prueba" --ano "2023"
```

## Estructura de Salida del Vault Atómico

El programa generará un vault de Obsidian en el directorio especificado por `--atomic_output_dir` (por defecto `D:\github\Libros Atomicos`). La estructura será la siguiente:

```
D:\github\Libros Atomicos/
└── [Año] - [Título del Libro] - [Autor]/
    ├── MOC - [Título del Libro].md             # MOC principal del libro
    ├── Capítulo 01 - [Título del Capítulo]/    # Carpeta para el Capítulo 01
    │   ├── MOC - [Título del Capítulo].md      # MOC del Capítulo 01
    │   ├── 1.1 - [Concepto Atómico 1].md       # Nota atómica 1.1
    │   ├── 1.2 - [Concepto Atómico 2].md       # Nota atómica 1.2
    │   └── ...
    ├── Capítulo 02 - [Título del Capítulo]/    # Carpeta para el Capítulo 02
    │   ├── MOC - [Título del Capítulo].md
    │   ├── 2.1 - [Concepto Atómico 1].md
    │   └── ...
    └── ...
```

Cada nota atómica (`.md`) contendrá:
*   **YAML Frontmatter:** Con metadatos como `tags`, `resumen`, `alias`, `fuente`, y `dominio/sub-dominio`.
*   **Contenido:** El texto destilado del concepto.
*   **Pie de Página de Navegación:** Un bloque con `dataviewjs` para navegar entre conceptos del mismo capítulo y enlaces de retorno a los MOCs.

Los MOCs de capítulo y el MOC principal contendrán scripts `dataviewjs` para listar y organizar las notas y capítulos de forma dinámica.