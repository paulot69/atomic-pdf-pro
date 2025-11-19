# PDF Atomic Pro: Edición Inteligente

## Descripción

**PDF Atomic Pro** ha sido rediseñado para ser una herramienta de procesamiento de conocimiento de alta precisión. Su misión es transformar un archivo PDF en un **Vault de Obsidian perfectamente estructurado, navegable y fiel al contenido original**, basándose en una interpretación experta del índice del libro.

Esta versión abandona la simple extracción para adoptar una filosofía donde **la estructura del índice del autor es la ley**. El resultado es un conjunto de notas atómicas limpias, interconectadas y enriquecidas con metadatos inteligentes, listas para una gestión del conocimiento seria.

## Características Principales

-   **Detección de Índice Experta:** Utiliza un sistema de tres capas para encontrar y jerarquizar el índice del libro, asegurando que la estructura de carpetas sea un reflejo fiel de la obra original.
    1.  **Bookmarks del PDF:** Máxima prioridad. Si existen, se convierten en la estructura maestra.
    2.  **Búsqueda Textual Inteligente:** Busca en español, inglés y portugués palabras clave como "Índice" o "Contents" al principio y al final del documento.
    3.  **Análisis Estructural:** Como último recurso, detecta patrones de texto (título + número de página) para inferir el índice.
    4.  **Fallback Robusto:** Si no se encuentra un índice fiable, procesa el libro secuencialmente y lo marca con el prefijo `[FI]` (Estructura Inferida).

-   **Normalización del Contenido:** Aplica un riguroso proceso de limpieza para garantizar la legibilidad sin alterar la redacción del autor.
    -   Reconstrucción de párrafos.
    -   Eliminación de encabezados y pies de página.
    -   Limpieza de artefactos de OCR y dobles espacios.

-   **Sistema de Tags Inteligente:** Cada nota se enriquece con dos tipos de tags:
    -   **Tags Estructurales (Automáticos):** `libro/titulo-del-libro`, `capitulo/nombre-del-capitulo` para una organización jerárquica.
    -   **Tags Semánticos (Opcionales):** Extrae de 1 a 3 palabras clave del contenido para facilitar el descubrimiento de temas.

-   **Traducción Opcional:** Permite traducir el contenido del libro a otro idioma de forma controlada a través de un comando específico.

-   **Verificación de Integridad:** Al finalizar, un módulo audita todos los `[[wikilinks]]` generados para garantizar que no haya ningún enlace roto dentro del vault.

-   **Navegación Fluida:** Genera Mapas de Contenido (MOCs) y pies de página con scripts `dataviewjs` para una exploración intuitiva entre notas y capítulos.

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

## Uso Simplificado

El programa ha sido rediseñado para ser fácil de usar, requiriendo solo la ruta al PDF.

**Sintaxis Principal:**
```bash
python main.py <ruta_al_pdf>
```

**Comportamiento:**
1.  El programa intentará extraer automáticamente el **título, autor y año** de los metadatos del archivo PDF.
2.  Si falta algún dato, **te lo preguntará interactivamente** en la consola.
3.  El vault de Obsidian se generará por defecto en `D:\github\Libros Atomicos`.

**Ejemplo:**
```bash
python main.py "D:\Mis Libros\Clean Code.pdf"
```

### Uso Avanzado (Personalizado)

Si deseas anular el comportamiento automático, puedes usar los siguientes argumentos:

**Sintaxis Avanzada:**
```bash
python main.py <ruta_al_pdf> [--titulo "<Título>"] [--autor "<Autor>"] [--ano "<Año>"] [--salida "<Ruta>"] [--traducir-a "<idioma>"]
```

**Argumentos Opcionales:**
-   `--titulo`: Especifica un título diferente.
-   `--autor`: Especifica un autor diferente.
-   `--ano`: Especifica un año diferente.
-   `--salida`: Define una ruta de salida personalizada para el vault atómico.
-   `--traducir-a`: Activa la traducción. Ejemplo: `--traducir-a "es"` para traducir a español.
-   `--sin-ia`: (V2.0+) Desactiva la generación de resúmenes y tags con IA, usando el método de fallback local.

## Automatización con Google Sheets

Para un procesamiento en lote y centralizado, puedes usar `sheet_runner.py` para orquestar la creación de vaults directamente desde una hoja de cálculo de Google Sheets.

**Sintaxis:**
```bash
# Procesar todos los libros nuevos marcados en la hoja
python sheet_runner.py

# Procesar todos los libros nuevos sin usar la IA
python sheet_runner.py --sin-ia
```

### Configuración

1.  **Preparar la Hoja de Google:**
    *   Asegúrate de que tu hoja de cálculo tenga, como mínimo, las siguientes columnas:
        *   `ATOMIZAR LIBRO.` (para marcar con "SI" los libros a procesar).
        *   `URL LOCAL` (con la ruta completa al archivo PDF en tu sistema).
        *   `Título Original del Libro`
        *   `Autor (Nombre Apellido)`
        *   `Año de Publicación`

2.  **Publicar la Hoja como CSV:**
    *   En Google Sheets, ve a `Archivo` > `Compartir` > `Publicar en la web`.
    *   En la ventana que aparece, selecciona `Toda la hoja` (o la hoja específica que quieres usar).
    *   En el menú desplegable, elige `Valores separados por comas (.csv)`.
    *   Haz clic en `Publicar`.
    *   Copia el enlace generado. Será algo como: `https://docs.google.com/spreadsheets/d/e/.../pub?output=csv`.

3.  **Configurar el `.env`:**
    *   Abre tu archivo `.env` (o crea uno a partir de `.env.example`).
    *   Pega el enlace que copiaste en la variable `SHEET_CSV_URL`.
    *   Asegúrate también de que tu `GEMINI_API_KEY` esté configurada si deseas usar la generación de metadatos por IA.

    ```dotenv
    GEMINI_API_KEY=tu_clave_de_api_aqui
    SHEET_CSV_URL=https://docs.google.com/spreadsheets/d/e/.../pub?output=csv
    ```

Una vez configurado, simplemente ejecuta `python sheet_runner.py` y el script se encargará de buscar, validar y procesar todos los libros que hayas marcado.

## Estructura de Salida del Vault

La estructura generada es predecible y organizada:

```
[Directorio de Salida]/
└── [Año] - [Título del Libro] - [Autor]/
    ├── MOC - [Título del Libro].md
    ├── Capítulo 01 - [Título del Capítulo]/
    │   ├── MOC - [Título del Capítulo].md
    │   ├── 1.1 - [Concepto Atómico 1].md
    │   └── ...
    └── ...
```
