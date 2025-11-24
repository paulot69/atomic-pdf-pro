---
tags: MOC
aliases: ["Resumen Capítulo {{chapter_number}} - {{chapter_title}}"]
---
# MOC - Capítulo {{ chapter_number }}: {{ chapter_title }}

[Resumen de los argumentos e ideas principales del capítulo.]

### _Conceptos Clave en este Capítulo:_

```dataviewjs
const currentFolderPath = dv.current().file.folder;
const pages = dv.pages(`"${currentFolderPath}"`) 
  .where(p => !p.file.name.startsWith("MOC"))
  .sort(p => p.file.name, 'asc');

const style = dv.el("style", `
.card { background-color: var(--background-secondary); border: 1px solid var(--background-modifier-border); padding: 14px 18px; border-radius: 8px; margin: 0 auto 12px auto; width: 100%; max-width: 700px; }
.card-title { font-weight: 600; font-size: 1.3em; margin-bottom: 6px; text-align: left; }
.card-title a { text-decoration: none !important; color: var(--text-accent) !important; display: inline-block; text-align: left; }
.card-summary { font-size: 0.9em; color: var(--text-muted); text-align: left; }
`);

for (const page of pages) {
  const resumen = page.resumen || "Sin resumen disponible.";
  const card = dv.el("div", "", {cls: "card"});
  const title = dv.el("div", dv.fileLink(page.file.path, false, page.file.name.replace('.md','') ), {cls: "card-title"});
  const summary = dv.el("div", resumen, {cls: "card-summary"});
  card.appendChild(title);
  card.appendChild(summary);
  dv.container.appendChild(card);
}
```

---
_Volver al [[{{ book_moc_filename }}]]_
