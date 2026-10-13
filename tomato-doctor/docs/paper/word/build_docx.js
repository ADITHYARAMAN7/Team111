/* build_docx.js - paper.json (from tex2json.py) -> IEEE-format Word document.
   Equations are written as placeholders and replaced with native OMML by
   finalize.py.  Run:  node build_docx.js  (NODE_PATH must contain docx)   */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, BorderStyle,
  AlignmentType, SectionType, TabStopType, Tab, HeadingLevel, LevelFormat, VerticalAlign, ShadingType,
  FrameAnchorType, FrameWrap, HorizontalPositionAlign, VerticalPositionAlign,
} = require("docx");

const HERE = __dirname;
const doc = JSON.parse(fs.readFileSync(path.join(HERE, "paper.json"), "utf8"));

// ---------------------------------------------------------------- geometry (US Letter, IEEE conference)
const PAGE_W = 12240, PAGE_H = 15840;
const MARGIN = { top: 1080, bottom: 1440, left: 893, right: 893 };   // 0.75", 1", 0.62"
const TEXT_W = PAGE_W - MARGIN.left - MARGIN.right;                   // 10454 DXA = 7.26"
const COL_GAP = 245;                                                   // 0.17"
const COL_W = Math.floor((TEXT_W - COL_GAP) / 2);                      // 5104 DXA
const DXA_PX = 96 / 1440;
const COL_PX = Math.floor(COL_W * DXA_PX) - 4;
const WIDE_PX = Math.floor(TEXT_W * DXA_PX) - 4;
const FONT = "Times New Roman";
const TAMIL = "Nirmala UI";

const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const RULE = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: "000000" });

// ---------------------------------------------------------------- runs
function runs(rs, base = {}) {
  return (rs || []).map((r) => {
    const o = { text: r.t, ...base };
    if (r.i) o.italics = true;
    if (r.b) o.bold = true;
    if (r.sc) o.smallCaps = true;
    if (r.sub) o.subScript = true;
    if (r.sup) o.superScript = true;
    if (r.sf) o.font = "Arial";
    if (r.tt) o.font = "Courier New";
    if (r.ta) o.font = { ascii: TAMIL, hAnsi: TAMIL, cs: TAMIL, eastAsia: TAMIL };
    if (base.size) o.sizeComplexScript = base.size;
    if (r.sf && base.size) o.size = base.size - 2;          // sans is visually larger
    return new TextRun(o);
  });
}
const plain = (rs) => (rs || []).map((r) => r.t).join("");

// ---------------------------------------------------------------- images
function imgSize(file) {
  const buf = fs.readFileSync(file);
  return { buf, w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };     // PNG IHDR
}
function image(file, maxW, maxH = 99999) {
  const { buf, w, h } = imgSize(path.join(HERE, file));
  let W = maxW, H = Math.round((h / w) * maxW);
  if (H > maxH) { H = maxH; W = Math.round((w / h) * maxH); }
  return new ImageRun({ type: "png", data: buf, transformation: { width: W, height: H },
    altText: { title: path.basename(file), description: path.basename(file), name: path.basename(file) } });
}

// ---------------------------------------------------------------- block builders
const body = (rs) => new Paragraph({ style: "Body", children: runs(rs) });

function heading(b) {
  if (b.type === "h1") {
    const kids = b.num ? [new TextRun({ text: `${b.num}. ` })] : [];
    return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [...kids, ...runs(b.runs, { smallCaps: true })] });
  }
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: `${b.num}. `, italics: true }), ...runs(b.runs, { italics: true })] });
}

// display equation: borderless 2-cell row, display-style OMML left, number right (IEEE Word convention)
function equation(b) {
  const numW = 520;
  const nb = { top: NONE, bottom: NONE, left: NONE, right: NONE };
  return new Table({
    width: { size: COL_W, type: WidthType.DXA }, columnWidths: [COL_W - numW, numW],
    borders: { ...nb, insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({ cantSplit: true, children: [
      new TableCell({ width: { size: COL_W - numW, type: WidthType.DXA }, borders: nb, verticalAlign: VerticalAlign.CENTER,
        margins: { top: 40, bottom: 40, left: 0, right: 0 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [new TextRun({ text: `@@EQ${b.num}@@` })] })] }),
      new TableCell({ width: { size: numW, type: WidthType.DXA }, borders: nb, verticalAlign: VerticalAlign.CENTER,
        margins: { top: 0, bottom: 0, left: 0, right: 0 },
        children: [new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 0 }, children: [new TextRun({ text: `(${b.num})` })] })] }),
    ] })],
  });
}

function caption(prefix, rs) {
  return new Paragraph({ style: "Caption", children: [new TextRun({ text: prefix, size: 16 }), ...runs(rs, { size: 16 })] });
}

// full-width figures float to the top of the page, spanning both columns (like LaTeX figure*)
const TOP_FRAME = {
  type: "alignment", alignment: { x: HorizontalPositionAlign.CENTER, y: VerticalPositionAlign.TOP },
  anchor: { horizontal: FrameAnchorType.MARGIN, vertical: FrameAnchorType.MARGIN }, width: TEXT_W, wrap: FrameWrap.NOT_BESIDE,
};

function wideFigure(b) {
  const out = [];
  if (b.layout === "row") {
    const dims = b.items.map((it) => imgSize(path.join(HERE, it.img)));
    const gapPx = 12;
    const sumAspect = dims.reduce((s, d) => s + d.w / d.h, 0);
    const H = Math.min(235, Math.floor((WIDE_PX - gapPx * (b.items.length - 1) - 8) / sumAspect));
    const ws = dims.map((d) => Math.round((d.w / d.h) * H));
    const total = ws.reduce((a, c) => a + c, 0) + gapPx * (b.items.length - 1);
    const left = Math.floor((WIDE_PX - total) / 2);
    const kids = [];
    if (left > 0) kids.push(new TextRun({ text: "" }));
    b.items.forEach((it, k) => {
      kids.push(image(it.img, ws[k], H));
      if (k < b.items.length - 1) kids.push(new TextRun({ text: "  " }));
    });
    out.push(new Paragraph({ frame: TOP_FRAME, alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 }, keepNext: true, children: kids }));
    // sub-captions centred under each image with centre tab stops
    let x = left;
    const stops = ws.map((w, k) => { const c = x + w / 2; x += w + gapPx; return { type: TabStopType.CENTER, position: Math.round(c / DXA_PX) }; });
    const capKids = [];
    b.items.forEach((it, k) => { capKids.push(new TextRun({ children: [new Tab()], size: 16 })); capKids.push(new TextRun({ text: `(${String.fromCharCode(97 + k)}) `, size: 16 }), ...runs(it.subcaption, { size: 16 })); });
    out.push(new Paragraph({ frame: TOP_FRAME, tabStops: stops, spacing: { after: 60 }, keepNext: true, children: capKids }));
  } else {
    b.items.forEach((it) => out.push(new Paragraph({ frame: TOP_FRAME, alignment: AlignmentType.CENTER, spacing: { after: 60 }, keepNext: true, children: [image(it.img, WIDE_PX - 8)] })));
  }
  out.push(new Paragraph({ frame: TOP_FRAME, style: "Caption", keepNext: false, spacing: { before: 40, after: 200 },
    children: [new TextRun({ text: `Fig. ${b.number}. `, size: 16 }), ...runs(b.caption, { size: 16 })] }));
  return out;
}

function figure(b) {
  const maxW = b.wide ? WIDE_PX : COL_PX;
  const out = [];
  if (b.layout === "row") {
    // side-by-side sub-figures in a borderless table, all scaled to the same height
    const dims = b.items.map((it) => imgSize(path.join(HERE, it.img)));
    const gap = 10;
    const sumAspect = dims.reduce((s, d) => s + d.w / d.h, 0);
    const H = Math.min(240, Math.floor((maxW - gap * b.items.length) / sumAspect));
    const widths = dims.map((d) => Math.round((d.w / d.h) * H) + gap);
    const total = widths.reduce((a, c) => a + c, 0);
    const colDxa = widths.map((w) => Math.floor((w / total) * TEXT_W));
    colDxa[colDxa.length - 1] += TEXT_W - colDxa.reduce((a, c) => a + c, 0);
    out.push(new Table({
      width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: colDxa,
      borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
      rows: [new TableRow({ children: b.items.map((it, k) => new TableCell({
        width: { size: colDxa[k], type: WidthType.DXA }, verticalAlign: VerticalAlign.BOTTOM,
        borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, children: [image(it.img, Math.round((dims[k].w / dims[k].h) * H), H)] }),
          new Paragraph({ style: "SubCaption", children: [new TextRun({ text: `(${String.fromCharCode(97 + k)}) ` }), ...runs(it.subcaption, { size: 16 })] }),
        ] })) })],
    }));
  } else {
    b.items.forEach((it, k) => {
      out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60 }, keepNext: true, children: [image(it.img, maxW)] }));
      if (it.subcaption) out.push(new Paragraph({ style: "SubCaption", keepNext: true, children: [new TextRun({ text: `(${String.fromCharCode(97 + k)}) ` }), ...runs(it.subcaption, { size: 16 })] }));
    });
  }
  out.push(caption(`Fig. ${b.number}. `, b.caption));
  return out;
}

function table(b) {
  const ncol = b.aligns.length;
  // column widths proportional to the longest cell text (capped), summing to the column width
  const len = Array(ncol).fill(6);
  b.rows.filter((r) => !r.note).forEach((r) => r.cells.forEach((c, k) => { len[k] = Math.max(len[k], Math.min(plain(c).length, 38)); }));
  const tot = len.reduce((a, c) => a + c, 0);
  const widths = len.map((l) => Math.floor((l / tot) * COL_W));
  widths[ncol - 1] += COL_W - widths.reduce((a, c) => a + c, 0);
  const align = { left: AlignmentType.LEFT, center: AlignmentType.CENTER, right: AlignmentType.RIGHT };
  const realRows = b.rows;
  const lastData = Math.max(...realRows.map((r, i) => (r.note ? -1 : i)));
  const rows = realRows.map((r, i) => {
    const top = i === 0 ? RULE(12) : b.mid_rows.includes(i) ? RULE(4) : NONE;
    const bottom = i === lastData ? RULE(12) : NONE;
    const borders = { top, bottom, left: NONE, right: NONE };
    if (r.note) {
      return new TableRow({ children: [new TableCell({ columnSpan: ncol, width: { size: COL_W, type: WidthType.DXA }, borders: { top: NONE, bottom: NONE, left: NONE, right: NONE },
        margins: { top: 30, bottom: 0, left: 40, right: 40 },
        children: [new Paragraph({ spacing: { after: 0 }, children: runs(r.cells[0], { size: 13 }) })] })] });
    }
    const keep = i < realRows.length - 1;          // keep the whole table on one page / column
    return new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.cells.map((c, k) => new TableCell({
      width: { size: widths[k], type: WidthType.DXA }, borders, margins: { top: 20, bottom: 20, left: 50, right: 50 },
      children: [new Paragraph({ alignment: align[b.aligns[k]] || AlignmentType.LEFT, keepNext: keep, keepLines: true, spacing: { after: 0 }, children: runs(c, { size: 16 }) })],
    })) });
  });
  return [
    new Paragraph({ style: "TableNumber", keepNext: true, children: [new TextRun({ text: `TABLE ${b.number}` })] }),
    new Paragraph({ style: "TableTitle", keepNext: true, children: runs(b.caption, { smallCaps: true, size: 16 }) }),
    new Table({ width: { size: COL_W, type: WidthType.DXA }, columnWidths: widths, rows,
      borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE } }),
    new Paragraph({ spacing: { after: 120 }, children: [] }),
  ];
}

function algorithm(b) {
  const out = [new Paragraph({
    keepNext: true, spacing: { before: 120, after: 40 }, border: { top: RULE(12), bottom: RULE(6) },
    children: [new TextRun({ text: `Algorithm ${b.number} `, bold: true, size: 18 }), ...runs(b.caption, { size: 18 })] })];
  b.lines.forEach((l, idx) => {
    const last = idx === b.lines.length - 1;
    const kids = [];
    kids.push(new TextRun({ text: l.n ? `${l.n}:` : "", size: 16 }));
    kids.push(new TextRun({ children: [new Tab()], size: 16 }));
    if (l.level) kids.push(new TextRun({ text: "  ".repeat(l.level), size: 16 }));
    kids.push(...runs(l.runs, { size: 16 }));
    if (l.comment && l.comment.length) {
      kids.push(new TextRun({ children: [new Tab()], size: 16 }), new TextRun({ text: "▷ ", size: 16 }), ...runs(l.comment, { size: 16 }));
    }
    out.push(new Paragraph({
      keepNext: !last, keepLines: true, spacing: { after: 0, line: 228 },
      tabStops: [{ type: TabStopType.LEFT, position: 300 }, { type: TabStopType.RIGHT, position: COL_W - 20 }],
      indent: { left: l.n ? 300 : 0, hanging: l.n ? 300 : 0 },
      border: last ? { bottom: RULE(12) } : undefined, children: kids }));
  });
  out.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
  return out;
}

function list(b) {
  return b.items.map((it) => new Paragraph({
    style: "Body", numbering: { reference: b.ordered ? "contrib" : "bullets", level: 0 }, indent: { left: 360, hanging: 260 },
    children: runs(it) }));
}

// ---------------------------------------------------------------- assemble sections
const sections = [];
const twoCol = { column: { count: 2, space: COL_GAP, equalWidth: true } };
const pageProps = { page: { size: { width: PAGE_W, height: PAGE_H }, margin: MARGIN } };

// title block (single column)
const titleBlock = [
  new Paragraph({ style: "Title", children: runs(doc.title) }),
  new Paragraph({ style: "AuthorName", children: [new TextRun("Author Name*, Author Name*, Author Name*, and Guide Name†")] }),
  new Paragraph({ style: "Affiliation", children: [new TextRun("*Department of Computer Science and Engineering, Institution Name, City, India")] }),
  new Paragraph({ style: "Affiliation", children: [new TextRun("†Department, Institution Name, City, India")] }),
  new Paragraph({ style: "Affiliation", spacing: { after: 360 }, children: [new TextRun("Email: {author1, author2}@institution.edu")] }),
];
sections.push({ properties: { ...pageProps }, children: titleBlock });

let current = [];
const flush = () => { if (current.length) { sections.push({ properties: { ...pageProps, type: SectionType.CONTINUOUS, ...twoCol }, children: current }); current = []; } };

// LaTeX floats figure* to the top of a following page; in Word we anchor the
// top-of-page frame a few paragraphs later so the current page fills first.
const WIDE_DEFER = 2;
const pendingWide = [];
for (const b of doc.blocks) {
  if (b.type === "p" && pendingWide.length) {
    pendingWide[0].wait -= 1;
    if (pendingWide[0].wait < 0) current.push(...wideFigure(pendingWide.shift().fig));
  }
  switch (b.type) {
    case "abstract":
      current.push(new Paragraph({ style: "Abstract", children: [new TextRun({ text: "Abstract—", italics: true, bold: true }), ...runs(b.runs, { bold: true })] }));
      break;
    case "keywords":
      current.push(new Paragraph({ style: "Abstract", spacing: { after: 160 }, children: [new TextRun({ text: "Index Terms—", italics: true, bold: true }), ...runs(b.runs, { bold: true })] }));
      break;
    case "h1": case "h2": current.push(heading(b)); break;
    case "p": current.push(body(b.runs)); break;
    case "list": current.push(...list(b)); break;
    case "equation": current.push(equation(b)); break;
    case "table": current.push(...table(b)); break;
    case "algorithm": current.push(...algorithm(b)); break;
    case "figure":
      if (b.wide) pendingWide.push({ fig: b, wait: WIDE_DEFER });
      else current.push(...figure(b));
      break;
    default: break;
  }
}
while (pendingWide.length) current.push(...wideFigure(pendingWide.shift().fig));
// references
current.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: "References", smallCaps: true })] }));
for (const r of doc.refs) {
  current.push(new Paragraph({ style: "Reference", tabStops: [{ type: TabStopType.LEFT, position: 360 }],
    children: [new TextRun({ text: `[${r.n}]` }), new TextRun({ children: [new Tab()] }), ...runs(r.runs, { size: 16 })] }));
}
flush();

// ---------------------------------------------------------------- styles
const document = new Document({
  creator: "Tomato Doctor authors",
  title: plain(doc.title),
  description: "IEEE conference paper - Word version",
  styles: {
    default: { document: { run: { font: FONT, size: 20 }, paragraph: { spacing: { after: 0, line: 240 } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 48 },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240, line: 276 } } },
      { id: "AuthorName", name: "Author Name", basedOn: "Normal", run: { size: 22 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 40 } } },
      { id: "Affiliation", name: "Affiliation", basedOn: "Normal", run: { size: 20 }, paragraph: { alignment: AlignmentType.CENTER } },
      { id: "Body", name: "Body Text IEEE", basedOn: "Normal", run: { size: 20 },
        paragraph: { alignment: AlignmentType.BOTH, indent: { firstLine: 288 }, spacing: { after: 0, line: 240 } } },
      { id: "Abstract", name: "Abstract", basedOn: "Normal", run: { size: 18, bold: true },
        paragraph: { alignment: AlignmentType.BOTH, indent: { firstLine: 202 }, spacing: { after: 80 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Body", quickFormat: true, run: { font: FONT, size: 20, smallCaps: true, color: "000000" },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Body", quickFormat: true, run: { font: FONT, size: 20, italics: true, color: "000000" },
        paragraph: { alignment: AlignmentType.LEFT, spacing: { before: 140, after: 60 }, keepNext: true, outlineLevel: 1 } },
      { id: "Equation", name: "Equation", basedOn: "Normal", run: { size: 20 }, paragraph: { spacing: { before: 80, after: 80 } } },
      { id: "Caption", name: "Caption", basedOn: "Normal", run: { size: 16 }, paragraph: { alignment: AlignmentType.BOTH, spacing: { before: 60, after: 180 } } },
      { id: "SubCaption", name: "Subfigure Caption", basedOn: "Normal", run: { size: 16 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 20, after: 60 } } },
      { id: "TableNumber", name: "Table Number", basedOn: "Normal", run: { size: 16 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 0 } } },
      { id: "TableTitle", name: "Table Title", basedOn: "Normal", run: { size: 16, smallCaps: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 80 } } },
      { id: "Reference", name: "Reference", basedOn: "Normal", run: { size: 16 },
        paragraph: { alignment: AlignmentType.BOTH, indent: { left: 360, hanging: 360 }, spacing: { after: 30 } } },
    ],
  },
  numbering: { config: [
    { reference: "contrib", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1)", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 260 } } } }] },
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 200 } } } }] },
  ] },
  sections,
});

Packer.toBuffer(document).then((buf) => {
  const out = path.join(HERE, "draft.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out, sections.length, "sections");
});
