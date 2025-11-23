# 🌲 **PDF Atomic Pro — Roadmap Profesional**

Objetivo:
Convertir lo que hoy es un proyecto poderoso pero “artesanal” en **una aplicación local profesional, estable, robusta, con interfaz completa y ejecutable**, sin depender de servidores externos ni infraestructura pagada.

# 🚀 Guía de Instalación y Uso

### 📋 Requisitos Previos

1.  **Docker Desktop** (para Windows/macOS) o **Docker Engine** (para Linux).

### 🐳 Ejecución con Docker (Modo Profesional)

PDF Atomic Pro puede ejecutarse completamente dentro de un contenedor Docker, incluyendo OCR, FastAPI y la interfaz web local. No necesitas instalar Python, Tesseract o Poppler en tu sistema.

**Paso 1 — Construir la imagen de Docker**

Desde la raíz del proyecto (`D:\02_DEV_LAB\00_GITHUB_REPOS\atomic-pdf-pro`), abre tu terminal y ejecuta:

```bash
docker build -t pdf-atomic-pro .
```
*Este comando crea una imagen local llamada `pdf-atomic-pro` que contiene todo lo necesario para ejecutar la aplicación.*

**Paso 2 — Preparar carpetas locales para datos**

Crea las siguientes carpetas en tu sistema anfitrión. Estas serán utilizadas por el contenedor para leer tus PDFs y guardar los resultados. Te recomiendo esta estructura:

```
D:\DOCKER_DATA\
   pdf_atomic_pro\input\  (Coloca aquí tus PDFs para procesar)
   pdf_atomic_pro\output\ (Aquí se guardarán los Libros Atómicos generados)
   pdf_atomic_pro\config\ (Opcional, si deseas sobreescribir configuraciones, ej. settings.json)
```

**Paso 3 — Iniciar la Aplicación Web**

Ejecuta el siguiente comando en tu terminal. Este comando mapea los puertos y volúmenes:

```bash
docker run --rm -p 8080:8080 \
  -v "G:\Mi unidad\06_BIBLIOTECA_DIGITAL:/input" \
  -v "D:\LibrosAtomicosOutput:/output" \
  pdf-atomic-pro
```

Una vez ejecutado, **abre tu navegador web y ve a: `http://127.0.0.1:8080`**

*La interfaz funciona exactamente igual que en modo local, pero ahora es completamente portátil.*

**Notas Importantes:**

*   `/input` y `/output` son las rutas **dentro del contenedor** que se corresponden con tus carpetas locales mapeadas.
*   Puedes copiar archivos desde la UI o seleccionar libros desde `/input`.
*   Los resultados se guardarán siempre en `/output`.
*   Para detener la aplicación, presiona `Ctrl+C` en la terminal donde ejecutaste `docker run` o usa `docker stop pdf_atomic_app` en otra terminal.

---

# ⭐ **FASE 0 — Consolidación Conceptual**

*(Antes de tocar una línea de código)*

### 1. Definir misión del programa (clara y breve)

* Convertir cualquier PDF en un **Libro Atómico** Obsidian-style.
* Mantener la voz del autor intacta.
* Crear estructura navegable (MOCs, carpetas, YAML).
* Ser 100% local, ejecutable y offline.

### 2. Establecer límites (para no caer en el síndrome del “agreguemos mil cosas”)

* No convertir imágenes a texto artístico.
* No resumir libros enteros.
* No inventar contenido inexistente.
* No crear interfaz compleja como un SaaS.

### 3. Mantener los módulos actuales, pero reorganizados.

---

# ⭐ **FASE 1 — Reorganizar el proyecto en arquitectura profesional (✅ COMPLETADO)**

Tu código ya es bueno. Pero ahora debe ser *ordenado como producto*.

### ✔ Estructura final del proyecto

```
pdf_atomic_pro/
│
├── core/                 ← Tu lógica actual (refinada)
│     ├── extractor/
│     ├── estructura/
│     ├── generacion/
│     ├── integridad/
│     ├── traduccion/
│     └── pipeline.py     ← process_pdf() unificado y limpio
│
├── api/
│     ├── server.py       ← FastAPI con endpoints
│     ├── models.py       ← Pydantic
│     └── workers.py      ← opcional: manejador de tareas en segundo plano
│
├── ui/
│     └── dist/           ← HTML, CSS, JS compilado y minificado
│
├── config/
│     ├── settings.json
│     ├── taxonomy_rules.txt
│     └── templates/*.yaml
│
├── logs/
│     └── ...
│
├── start_gui.py          ← arranca FastAPI + abre interfaz
├── requirements.txt
└── README.md
```

### ✔ Objetivos de esta fase

* Dejar el **pipeline limpio**, segmentado y testeable.
* Exponer funciones como API.
* Separar backend ↔ frontend.
* Eliminar dependencias globales o rutas quemadas.
* Preparar el terreno para el ejecutable.

**Duración estimada:** 1 semana.

---

# ⭐ **FASE 2 — Transformar el pipeline en una API real (FastAPI) (✅ COMPLETADO)**

### Endpoints esenciales

* `POST /process_pdf`
* `POST /preview_toc`
* `POST /extract_text_test`
* `POST /process_sheet`
* `GET /status/{task_id}`
* `GET /logs`

### Razones:

* Permite interfaz moderna.
* Permite ejecutable sin consola.
* Aísla errores.
* Facilita depuración.

### Extras recomendados

* Manejo de estado mediante `BackgroundTasks`.
* Sistema interno de “tareas” que permite barra de progreso real.
* Logs accesibles desde la UI.

**Duración estimada:** 1 semana.

---

# ⭐ **FASE 3 — Interfaz Web limpia y compacta (✅ COMPLETADO)**

Tu demo HTML ya es un gran comienzo, pero debe convertirse en una UI “productiva”:

### ✔ Pantallas necesarias

1. **Inicio**

   * cargar PDF
   * título/autor/año
   * activar/desactivar IA
   * btn: Procesar

2. **Panel de progreso**

   * barra
   * logs visibles
   * mensaje final

3. **Historial local**

   * lista de libros procesados
   * rutas
   * metadatos
   * botón para abrir carpeta

4. **Configuración**

   * plantilla YAML
   * idioma de salida
   * activar traducción
   * carpeta de salida

### ✔ Tecnologías sugeridas (todas gratuitas)

* Bootstrap 5 (rápido, simple).
* Vanilla JS (sin frameworks pesados).

**Duración estimada:** 1–2 semanas.

---

# ⭐ **FASE 4 — Sistema de Configuración y Plantillas (🚧 EN PROGRESO)**

Profesional = configurable.

### ✔ Agregar `config/settings.json`

Ejemplo:

```json
{
  "output_folder": "D:/Libros_Atomicos",
  "language": "es",
  "use_ai": true,
  "template_default": "standard.yaml"
}
```

### ✔ Plantillas YAML personalizables

En `config/templates/`.

### ✔ Taxonomía por archivo editable

`taxonomy_rules.txt`

**Duración:** 2 días.

---

# ⭐ **FASE 5 — Empaquetar como ejecutable (.exe)**

Sin esto, no hay “programa”, solo código.

### ✔ Usar Nuitka (recomendado)

Más limpio, más rápido, más difícil de romper.

Comando:

```
nuitka --standalone --onefile --follow-imports start_gui.py
```

Esto genera:

```
PDF-Atomic-Pro.exe
```

### ✔ Beneficios

* No requiere Python instalado.
* Inicia servidor local y abre el panel automáticamente.
* El usuario (tú) nunca ve una terminal negra.

**Duración:** 1 día.

---

# ⭐ **FASE 6 — Testing real con libros diversos**

### Tipos de PDF a probar:

* Libros con TOC perfecto.
* PDFs escaneados (OCR).
* PDFs con mucho subcapítulo.
* Manuales técnicos con tablas.
* Libros sin TOC (fallback).
* PDFs en inglés, español, mezclado.

### Verificar:

* Estructura del vault
* Enlaces rotos
* MOCs completos
* Detección de capítulos
* Integridad de notas atómicas

**Duración:** 1 semana, intermitente.

---

# ⭐ **FASE 7 — Calidad de vida y refinamientos**

### Mejoras opcionales:

* Sistema de “arrastrar y soltar” PDFs en la UI.
* Reporte visual del índice detectado.
* Editor visual de la taxonomía.
* Plantillas de exportación (académica / zettelkasten / mínima).

### Mejoras útiles:

* File watcher para abrir automáticamente Obsidian al terminar.
* Autoactualización de la UI sin recargar.

**Duración:** depende de tu energía y ganas.

---

# ⭐ **FASE 8 — Documentación final (personal)**

No es marketing; es claridad para *tu yo del futuro*.

Debe incluir:

1. arquitectura
2. cómo construir el ejecutable
3. cómo añadir plantillas
4. cómo se estructura un TOC
5. flujo interno

**Duración:** 1 día.

---

# ⭐ Resumen del roadmap (en modo ejecutivo)

1. **Reorganizar proyecto** (núcleos, API, UI separada).
2. **Crear API limpia con FastAPI**.
3. **Construir interfaz visual**.
4. **Agregar configuración editable y plantillas**.
5. **Empaquetar ejecutable (Nuitka)**.
6. **Hacer tests reales con distintos PDFs**.
7. **Mejoras de calidad de vida**.
8. **Documentación personal**.

Tiempo total estimado: **5–7 semanas de trabajo tranquilo y constante**.
(Rápido si trabajas con Jules a diario.)
