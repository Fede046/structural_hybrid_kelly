"""Genera la tesi in Word (.docx) dal Markdown, con la stessa impaginazione del PDF di build_tesi_latex.py.

thesis/TESI_kellybench.md -> thesis/Malservigi_Tesi_KellyBench.docx (nome in DELIVERABLE_NAMES di build_tesi_latex.py)

- Frontespizio Unibo con i dati di thesis/latex/frontespizio_kellybench.tex, poi Abstract e Indice con
  numeri di pagina romani; i capitoli ripartono da 1 in numeri arabi.
- Pagina bianca fra un capitolo e l'altro e fra l'indice e il capitolo 1; il §4.3 e il §7.2 su una
  pagina nuova; le figure del §5.4 una per pagina.
- Formule come equazioni di Word (con il numero a destra), citazioni numeriche [1, 2], tabelle con i
  filetti in alto, sotto l'intestazione e in fondo, e un filetto chiaro fra le righe di testo lungo.
- Bibliografia dalla lista numerata del Markdown, ringraziamenti da thesis/latex/ringraziamenti.tex.

Servono pandoc e python-docx:
    pip install pypandoc_binary python-docx

Uso, dalla radice del repository:
    .venv/Scripts/python.exe scripts/build_tesi_docx.py [--source thesis/ALTRA.md] [--pandoc PERCORSO] [--word]

Con --word il documento si apre in Microsoft Word per riempire l'indice (numeri di pagina) e salvarlo;
senza, Word chiede di aggiornare l'indice alla prima apertura.
"""
from __future__ import annotations

import argparse
import copy
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_tesi_latex import (DELIVERABLE_NAMES, FULL_PAGE_SECTIONS, NEW_PAGE_SECTIONS, NUMERIC, cell_size,  # noqa: E402
                              column_widths, is_portrait)

try:
    import docx
    from docx.enum.section import WD_SECTION
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:  # pragma: no cover
    raise SystemExit("Serve python-docx: pip install python-docx")

REPO = Path(__file__).resolve().parents[1]
THESIS = REPO / "thesis"
SOURCE = THESIS / "TESI_kellybench.md"
LATEX = THESIS / "latex"
FONT = "Times New Roman"
TEXT_WIDTH_CM = 15.0  # A4 con margini di 3 cm

PAGE_BREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'
# pagina bianca: un paragrafo vuoto che comincia una pagina; il titolo che segue va alla pagina dopo
BLANK = '```{=openxml}\n<w:p><w:pPr><w:pageBreakBefore/></w:pPr></w:p>\n```'
TOC = ('```{=openxml}\n<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>Indice</w:t></w:r></w:p>\n'
       '<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
       '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
       '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
       "<w:r><w:t>Indice da aggiornare: tasto destro, Aggiorna campo.</w:t></w:r>"
       '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>\n```')
SECTION_MARK = "SEZIONE-ROMANA-FINE"  # paragrafo segnaposto: qui finisce la parte con i numeri romani


# ---------- dal Markdown della tesi al Markdown per pandoc ----------
def find_pandoc(given: str | None) -> str:
    if given and Path(given).exists():
        return given
    found = shutil.which("pandoc")
    if found:
        return found
    try:
        import pypandoc  # noqa: F401
        exe = Path(pypandoc.__file__).parent / "files" / "pandoc.exe"
        if exe.exists():
            return str(exe)
    except ImportError:
        pass
    raise SystemExit("pandoc non trovato: pip install pypandoc_binary, oppure --pandoc PERCORSO")


def citation_order(md: str) -> list[str]:
    order: list[str] = []
    for tok in re.findall(r"\[@[^\]]+\]", md):
        for k in tok[1:-1].split(";"):
            k = k.strip().lstrip("@")
            if k not in order:
                order.append(k)
    return order


def pipe_table(rows: list[list[str]]) -> list[str]:
    """Tabella pipe con larghezze relative (numero di trattini) e colonne numeriche allineate a destra."""
    widths = column_widths(rows)
    total = sum(widths)
    seps = []
    for c, w in enumerate(widths):
        dashes = "-" * max(3, round(100 * w / total))
        numeric = all(NUMERIC.fullmatch(r[c].strip()) for r in rows[1:] if r[c].strip())
        seps.append(dashes[:-1] + ":" if numeric else dashes)
    return ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(seps) + "|"] + \
           ["| " + " | ".join(r) + " |" for r in rows[1:]]


def figure(path: str, caption: str, full_page: bool) -> str:
    m = re.match(r"(Figura\s+[\dA-Z]+\.\d+\.)\s*(.*)", caption)
    cap = f"**{m.group(1)}** {m.group(2)}" if m else caption
    portrait = is_portrait(THESIS / path)
    if full_page:
        size = "height=17.5cm" if portrait else f"width={TEXT_WIDTH_CM}cm"
    else:
        size = "width=12.5cm" if portrait else f"width={TEXT_WIDTH_CM}cm"
    return f"![{cap}]({path}){{{size}}}"


def to_pandoc(md: str) -> tuple[str, list[str]]:
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0
    while not lines[i].startswith("## "):  # titolo e indice scritto a mano
        i += 1
    body_md = "\n".join(lines[i:]).split("\n## Bibliografia")[0]
    cited = citation_order(body_md)
    number = {k: n for n, k in enumerate(cited, 1)}

    def cite(m: re.Match) -> str:
        keys = [k.strip().lstrip("@") for k in m.group(0)[1:-1].split(";")]
        return "\\[" + ", ".join(str(number[k]) for k in keys) + "\\]"

    out: list[str] = []
    in_appendix = False
    full_page = False
    fig_pages = False
    bib_intro: list[str] = []
    bib_items: list[str] = []
    in_bib = False
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if in_bib:
            item = re.match(r"^\d+\.\s+(.*)$", line)
            if item:
                bib_items.append(item.group(1).strip())
            elif s and not bib_items:
                bib_intro.append(s)
            i += 1
            continue
        if fig_pages and s and not line.startswith("!["):
            out.append(PAGE_BREAK)  # dopo le figure a pagina intera il testo riparte su una pagina nuova
            fig_pages = False
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if level <= 3:
                full_page = level == 3 and title.split(" ")[0] in FULL_PAGE_SECTIONS
            if level == 2:
                if title.startswith("0. "):
                    out.append(f"# {title[3:]}")
                elif title == "Appendici":
                    in_appendix = True
                elif title == "Bibliografia":
                    in_bib = True
                else:
                    if title.startswith("1. "):
                        # indice, poi una pagina bianca che chiude la parte con i numeri romani
                        out += [TOC, BLANK, SECTION_MARK]
                    else:
                        out.append(BLANK)  # pagina bianca fra due capitoli
                    out.append(f"# {title}")
            elif level == 3:
                if in_appendix:
                    out += [BLANK, f"# {title}"]
                else:
                    out.append(f"## {title}")
            else:
                out.append(f"### {title}")
            i += 1
            continue
        if s == "$$":
            j = lines.index("$$", i + 1)
            eq = "\n".join(lines[i + 1:j]).strip()
            tag = re.search(r"\\tag\{([^}]*)\}", eq)
            if tag:  # Word non conosce \tag: il numero va in fondo alla formula
                eq = eq.replace(tag.group(0), "").rstrip() + f" \\qquad ({tag.group(1)})"
            out.append(f"$$\n{eq}\n$$")
            i = j + 1
            continue
        if line.startswith("!["):
            path = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line).group(1)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            caption = ""
            if j < len(lines) and lines[j].startswith("*Figura"):
                caption = lines[j].strip().strip("*")
                i = j + 1
            else:
                i += 1
            if full_page:
                out.append(PAGE_BREAK)  # una pagina per figura
                fig_pages = True
            out.append(figure(path, re.sub(r"\[@[^\]]+\]", cite, caption), full_page))
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append([re.sub(r"\[@[^\]]+\]", cite, c) for c in cells])
                i += 1
            out.append("\n".join(pipe_table(rows)))
            continue
        # paragrafi, elenchi, citazioni in blocco: si copiano, con le citazioni numerate
        block = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#|\$\$$|!\[|\|)", lines[i]):
            block.append(re.sub(r"\[@[^\]]+\]", cite, lines[i]))
            i += 1
        if block:
            out.append("\n".join(block))
        else:
            i += 1

    if len(bib_items) != len(cited):
        raise SystemExit(f"La bibliografia del Markdown ha {len(bib_items)} voci, le citazioni sono {len(cited)}")
    out += [BLANK, "# Bibliografia", " ".join(bib_intro),
            '::: {custom-style="Bibliografia"}', *[f"\\[{n}\\]\u00a0{t}\n" for n, t in enumerate(bib_items, 1)],
            ":::"]
    thanks = LATEX / "ringraziamenti.tex"
    if thanks.exists():
        text = "\n".join(l for l in thanks.read_text(encoding="utf-8").splitlines() if not l.startswith("%"))
        text = text.replace("\\ ", " ").replace("~", "\u00a0")
        out += [BLANK, "# Ringraziamenti", text.strip()]
    return "\n\n".join(out) + "\n", cited


# ---------- stili del documento di riferimento ----------
def set_font(style, size: float, bold: bool | None = None, italic: bool | None = None) -> None:
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), FONT)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(attr), None)


def border(tag: str, size: int, color: str = "000000") -> OxmlElement:
    b = OxmlElement(f"w:{tag}")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(size))
    b.set(qn("w:space"), "0")
    b.set(qn("w:color"), color)
    return b


def reference_docx(pandoc: str, path: Path) -> None:
    subprocess.run([pandoc, "-o", str(path), "--print-default-data-file", "reference.docx"], check=True)
    d = docx.Document(str(path))
    st = d.styles
    for name in ("Normal", "Body Text", "First Paragraph"):
        set_font(st[name], 12)
    for name in ("Body Text", "First Paragraph"):
        pf = st[name].paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.space_before, pf.space_after = Pt(0), Pt(4)
        pf.line_spacing = 1.2
    st["Body Text"].paragraph_format.first_line_indent = Cm(0.5)
    set_font(st["Compact"], 12)
    st["Compact"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    st["Compact"].paragraph_format.space_after = Pt(3)
    st["Compact"].paragraph_format.line_spacing = 1.2
    for name, size, before, after in (("Heading 1", 24, 60, 30), ("Heading 2", 15, 18, 8), ("Heading 3", 12, 10, 4)):
        set_font(st[name], size, bold=True, italic=False)
        pf = st[name].paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.keep_with_next = True
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    st["Heading 1"].paragraph_format.page_break_before = True
    set_font(st["TOC Heading"], 24, bold=True)
    st["TOC Heading"].paragraph_format.space_before = Pt(60)
    st["TOC Heading"].paragraph_format.space_after = Pt(30)
    st["TOC Heading"].paragraph_format.page_break_before = True
    for name in ("Image Caption", "Table Caption"):
        set_font(st[name], 10, italic=False)
        st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        st[name].paragraph_format.space_after = Pt(12)
    st["Captioned Figure"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st["Captioned Figure"].paragraph_format.keep_with_next = True
    st["Figure"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(st["Block Text"], 11, italic=True)
    bib = st.add_style("Bibliografia", WD_STYLE_TYPE.PARAGRAPH)
    bib.base_style = st["Normal"]
    set_font(bib, 11)
    bib.paragraph_format.left_indent = Cm(0.9)
    bib.paragraph_format.first_line_indent = Cm(-0.9)
    bib.paragraph_format.space_after = Pt(5)
    bib.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # stile delle tabelle: filetto spesso in alto e in fondo, sottile sotto l'intestazione
    table = st["Table"].element
    tblpr = table.find(qn("w:tblPr"))
    if tblpr is None:
        tblpr = OxmlElement("w:tblPr")
        table.append(tblpr)
    for old in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(old)
    borders = OxmlElement("w:tblBorders")
    borders.append(border("top", 12))
    borders.append(border("bottom", 12))
    tblpr.append(borders)
    for cond in table.findall(qn("w:tblStylePr")):
        if cond.get(qn("w:type")) == "firstRow":
            table.remove(cond)
    first = OxmlElement("w:tblStylePr")
    first.set(qn("w:type"), "firstRow")
    rpr = OxmlElement("w:rPr")
    rpr.append(OxmlElement("w:b"))
    first.append(rpr)
    tcpr = OxmlElement("w:tcPr")
    tcb = OxmlElement("w:tcBorders")
    tcb.append(border("bottom", 6))
    tcpr.append(tcb)
    first.append(tcpr)
    table.append(first)
    d.save(str(path))


# ---------- ritocchi al documento prodotto da pandoc ----------
def field_run(paragraph, instr: str) -> None:
    for kind, text in (("begin", None), (None, instr), ("end", None)):
        run = paragraph.add_run()
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)


def front_data() -> dict[str, str]:
    path = LATEX / "frontespizio_kellybench.tex"
    if not path.exists():
        path = LATEX / "frontespizio.tex"
    data = {}
    for name, value in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}\s*$", path.read_text(encoding="utf-8"), re.M):
        value = re.sub(r"\\textcolor\{\w+\}\{([^}]*)\}", r"\1", value)
        value = value.replace("\\\\ ", " ").replace("\\\\", " ").replace("--", "\u2013").replace("~", "\u00a0")
        data[name] = value.strip()
    return data


def add_title_page(d: docx.document.Document) -> None:
    f = front_data()
    first = d.paragraphs[0]

    def para(text: str = "", size: float = 12, bold: bool = False, caps: bool = False, after: float = 0,
             before: float = 0, rule: int = 0):
        p = first.insert_paragraph_before()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(after)
        p.paragraph_format.first_line_indent = Cm(0)
        if text:
            r = p.add_run(text)
            r.font.name, r.font.size, r.bold, r.font.small_caps = FONT, Pt(size), bold, caps
        if rule:
            ppr = p._p.get_or_add_pPr()
            pbdr = OxmlElement("w:pBdr")
            pbdr.append(border("bottom", rule))
            ppr.append(pbdr)
        return p

    seal = LATEX / "sigillo_unibo.png"
    if seal.exists():
        para().add_run().add_picture(str(seal), width=Cm(3.2))
    para("Alma Mater Studiorum \u00b7 Università di Bologna", 14, caps=True, before=6, after=2, rule=4)
    para(f["Dipartimento"], 10, bold=True, before=10)
    para(f["CorsoDiLaurea"], 10, bold=True, after=70)
    para(f["Titolo"], 22, bold=True, after=10)
    para(f["Sottotitolo"], 16, bold=True, after=40)
    if f.get("Insegnamento"):
        para(f["Insegnamento"], 11, bold=True)
    para(after=150)
    tbl = d.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, (label, name, align) in zip(tbl.rows[0].cells, (("Relatore:", f["Relatore"], WD_ALIGN_PARAGRAPH.LEFT),
                                                             ("Presentata da:", f["Candidato"], WD_ALIGN_PARAGRAPH.RIGHT))):
        cell.width = Cm(TEXT_WIDTH_CM / 2)
        p = cell.paragraphs[0]
        p.alignment = align
        for k, text in enumerate((label, name)):
            r = p.add_run(text)
            r.font.name, r.font.size, r.bold = FONT, Pt(12), True
            if k == 0:
                r.add_break()
    borders = OxmlElement("w:tblBorders")  # la tabella del frontespizio serve solo a impaginare: niente filetti
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "nil")
        borders.append(b)
    tbl._tbl.tblPr.append(borders)
    first._p.addprevious(tbl._tbl)
    para(after=30)
    para(rule=12, after=12)
    para(f["Sessione"], 12, bold=True)
    para(f["AnnoAccademico"], 12, bold=True)


def section_break_before(paragraph, sect_pr) -> None:
    """Chiude la sezione con i numeri romani al posto del paragrafo segnaposto."""
    ppr = paragraph._p.get_or_add_pPr()
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    ppr.append(sect_pr)


def set_pagination(d: docx.document.Document) -> None:
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(3))
    sec.footer_distance = Cm(1.5)
    sec.start_type = WD_SECTION.NEW_PAGE
    footer = sec.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field_run(p, " PAGE ")
    sec.different_first_page_header_footer = True  # il frontespizio non ha numero
    sec.first_page_footer.paragraphs[0].text = ""
    body_sect = d.element.body.find(qn("w:sectPr"))
    roman = copy.deepcopy(body_sect)
    num = OxmlElement("w:pgNumType")
    num.set(qn("w:fmt"), "lowerRoman")
    num.set(qn("w:start"), "0")  # il frontespizio è la pagina 0: l'abstract è la i
    roman.append(num)
    # la sezione finale: numeri arabi da 1, senza prima pagina speciale
    for t in body_sect.findall(qn("w:titlePg")):
        body_sect.remove(t)
    num = OxmlElement("w:pgNumType")
    num.set(qn("w:fmt"), "decimal")
    num.set(qn("w:start"), "1")
    body_sect.append(num)
    mark = next(p for p in d.paragraphs if p.text.strip() == SECTION_MARK)
    section_break_before(mark, roman)


def keep_together(tbl, short: bool) -> None:
    rows = tbl.rows
    for k, row in enumerate(rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if k == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = short and k < len(rows) - 1
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(2), Pt(2)
                p.paragraph_format.line_spacing = 1.0
                if p.alignment != WD_ALIGN_PARAGRAPH.RIGHT:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.size = Pt(10.5 if len(tbl.columns) < 7 else 9.5)


def style_tables(d: docx.document.Document) -> None:
    for tbl in d.tables[1:]:  # la prima è quella del frontespizio
        text = [c.text for row in tbl.rows for c in row.cells]
        wordy = any(len(t) > 45 for t in text)
        short = sum(len(t) for t in text) < 2600 and len(tbl.rows) <= 25
        keep_together(tbl, short)
        tblpr = tbl._tbl.tblPr
        mar = OxmlElement("w:tblCellMar")
        for side, w in (("top", 40 if wordy else 0), ("bottom", 40 if wordy else 0), ("left", 100), ("right", 100)):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:w"), str(w))
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblpr.append(mar)
        # un po' d'aria fra il testo e la tabella, sopra e sotto
        prev, nxt = tbl._tbl.getprevious(), tbl._tbl.getnext()
        if prev is not None and prev.tag == qn("w:p"):
            docx.text.paragraph.Paragraph(prev, tbl._parent).paragraph_format.space_after = Pt(8)
        if nxt is not None and nxt.tag == qn("w:p"):
            docx.text.paragraph.Paragraph(nxt, tbl._parent).paragraph_format.space_before = Pt(12)
        if wordy:  # filetto chiaro fra una riga e l'altra
            borders = OxmlElement("w:tblBorders")
            borders.append(border("top", 12))
            borders.append(border("bottom", 12))
            borders.append(border("insideH", 4, "BFBFBF"))
            tblpr.append(borders)


def new_page_sections(d: docx.document.Document) -> None:
    for p in d.paragraphs:
        if p.style.name == "Heading 2" and p.text.split(" ")[0] in NEW_PAGE_SECTIONS:
            p.paragraph_format.page_break_before = True


def update_fields_on_open(d: docx.document.Document) -> None:
    settings = d.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)


def word_refresh(path: Path, pdf: Path | None) -> None:
    """Apre il documento in Word, riempie l'indice, salva; se richiesto esporta anche il PDF."""
    export = f'$d.ExportAsFixedFormat("{pdf}", 17)' if pdf else ""
    script = f"""
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {{
  $d = $w.Documents.Open("{path}")
  $d.Fields.Update() | Out-Null
  foreach ($t in $d.TablesOfContents) {{ $t.Update() }}
  $d.Save()
  {export}
  $d.Close()
}} finally {{ $w.Quit() }}
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--pandoc")
    ap.add_argument("--word", action="store_true", help="riempie l'indice con Microsoft Word")
    ap.add_argument("--pdf", help="con --word, esporta anche un PDF di controllo in questo percorso")
    args = ap.parse_args()
    source = Path(args.source)
    out = source.with_name(DELIVERABLE_NAMES.get(source.stem, source.stem) + ".docx")
    pandoc = find_pandoc(args.pandoc)
    text, _ = to_pandoc(source.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        md, ref = Path(tmp) / "tesi.md", Path(tmp) / "reference.docx"
        md.write_text(text, encoding="utf-8")
        reference_docx(pandoc, ref)
        subprocess.run([pandoc, str(md), "-f", "markdown", "-t", "docx", "--reference-doc", str(ref),
                        "--resource-path", str(THESIS), "--columns", "10", "-o", str(out)], check=True)
    d = docx.Document(str(out))
    add_title_page(d)
    set_pagination(d)
    style_tables(d)
    new_page_sections(d)
    update_fields_on_open(d)
    d.save(str(out))
    if args.word:
        update_off = docx.Document(str(out))
        for e in update_off.settings.element.findall(qn("w:updateFields")):
            update_off.settings.element.remove(e)
        update_off.save(str(out))
        word_refresh(out.resolve(), Path(args.pdf).resolve() if args.pdf else None)
    print("DOCX:", out)


if __name__ == "__main__":
    main()
