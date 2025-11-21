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

2.  **Configurar la IA (Opcional):**
    *   Abre tu archivo `.env`.
    *   Añade tu clave de API de Google Gemini a la variable `GEMINI_API_KEY`.
    *   Si dejas esta clave vacía, el programa funcionará en modo local (sin IA).

3.  **Configurar Google Sheets (Opcional, para modo en lote):**
    *   Abre tu hoja de cálculo y ve a `Archivo` > `Compartir` > `Publicar en la web`.
    *   Elige `Toda la hoja` (o la hoja específica) y `Valores separados por comas (.csv)`.
    *   Copia el enlace generado y pégalo en la variable `SHEET_CSV_URL` de tu archivo `.env`.

4.  **Personalizar la Taxonomía de la IA (Avanzado):**
    *   Puedes editar las reglas que sigue la IA para generar tags modificando el archivo: `config/taxonomy_rules.txt`.
    *   Esto te permite añadir o quitar dominios y ajustar las instrucciones sin tocar el código.

## Uso

El programa tiene dos modos de ejecución. Para el flujo de trabajo principal y automatizado, solo necesitas usar el **Modo 2**.

### Modo 1: Procesar un Solo PDF (Manual)

Este modo es útil para procesar un único archivo de forma rápida y aislada. Se utiliza el script `main.py`, que es el motor de procesamiento principal. Necesita que le pases la ruta del PDF directamente.

**Sintaxis:**
```bash
python main.py <ruta_al_pdf> [argumentos_opcionales]
```
**Ejemplo:**
```bash
python main.py "D:\Mis Libros\Clean Code.pdf"
```

### Modo 2: Procesar en Lote desde Google Sheets (Automático)

Este es el modo recomendado para el flujo de trabajo principal. Utiliza el script `sheet_runner.py`, que actúa como un orquestador: lee tu hoja de Google Sheets, encuentra los libros marcados con "SI" y llama a `main.py` por cada uno, pasándole automáticamente la ruta y los metadatos.

Con este modo, **no necesitas pasar ninguna ruta manualmente**.

**Sintaxis:**
```bash
# Procesar todos los libros nuevos marcados en la hoja
python sheet_runner.py

# Procesar todos los libros nuevos sin usar la IA
python sheet_runner.py --sin-ia
```

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

## Argumentos Opcionales (para `main.py`)
-   `--titulo`, `--autor`, `--ano`: Especifican los metadatos del libro.
-   `--salida`: Define una ruta de salida personalizada.
-   `--traducir-a`: Activa la traducción a un idioma (ej: "es").
-   `--sin-ia`: Desactiva la generación de metadatos con IA.

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
