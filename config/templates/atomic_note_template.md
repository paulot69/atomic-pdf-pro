---
tags:
  - status/desarrollo
  - archivo
  - tipo/referencia
  - fuente/{{author_lastname}}
  - {{domain_tag_placeholder}}
resumen: "{{ summary }}"
alias: ["{{ note_title }}"]
---
# {{ note_title }}

{{note_content}}

---
#### _Ver otros conceptos en este capítulo_:

```dataviewjs
const currentFilePath = dv.current().file.path;
const currentFolderPath = currentFilePath.substring(0, currentFilePath.lastIndexOf("/"));
const pages = dv.pages(`"${currentFolderPath}"`) 
  .where(p => p.file.path !== currentFilePath && !p.file.name.startsWith("MOC"))
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
_Volver al [[{{ chapter_moc_filename }}]]_
_Volver al [[{{ book_moc_filename }}]]_
