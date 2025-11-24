---
tags: MOC
aliases: ["Resumen {{book_title}}"]
---
# MOC - {{book_title}}

[Resumen general del libro, sus tesis centrales y por qué es relevante para el proyecto.]

### _Mapa de Contenido (Capítulos):_

```dataviewjs
const bookRoot = dv.current().file.folder;
const chapterMOCs = dv.pages(`"${bookRoot}"`)
  .where(p => p.file.name.startsWith("MOC_Cap_"))
  .sort(p => p.file.name, 'asc');

const style = dv.el("style", `
.card { background-color: var(--background-secondary); border: 1px solid var(--background-modifier-border); padding: 14px 18px; border-radius: 8px; margin: 0 auto 12px auto; width: 100%; max-width: 700px; }
.card-title { font-weight: 600; font-size: 1.3em; margin-bottom: 6px; text-align: left; }
.card-title a { text-decoration: none !important; color: var(--text-accent) !important; display: inline-block; text-align: left; }
.card-summary { font-size: 0.9em; color: var(--text-muted); text-align: left; }
`);

for (const moc of chapterMOCs) {
  const card = dv.el("div", "", {cls: "card"});
  const title = dv.el("div", dv.fileLink(moc.file.path, false, moc.file.name.replace('.md','').replace('MOC_Cap_', 'Capítulo ')), {cls: "card-title"});
  dv.container.appendChild(card);
}
```

---
### _Índice de Todos los Conceptos:_

```dataviewjs
const bookRoot = dv.current().file.folder;
const allAtomicNotes = dv.pages(`"${bookRoot}"`) 
  .where(p => !p.file.name.startsWith("MOC") && !p.file.folder.includes("METADATA"))
  .sort(p => p.file.name, 'asc');

dv.list(allAtomicNotes.map(p => dv.fileLink(p.file.path)));
```
