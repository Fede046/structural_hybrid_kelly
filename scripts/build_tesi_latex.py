"""Genera la tesi in LaTeX con il frontespizio dell'Università di Bologna, e la compila con Tectonic.

thesis/TESI.md -> thesis/latex/TESI_unibo.tex -> thesis/latex/TESI_unibo.pdf

- Frontespizio come nelle tesi Unibo (sigillo, dipartimento, corso, titolo, relatore, candidato,
  sessione, anno accademico); i dati sono in thesis/latex/frontespizio.tex, creato al primo
  avvio con dei segnaposto e poi mai sovrascritto.
- Ringraziamenti in fondo, se esiste thesis/latex/ringraziamenti.tex (mai sovrascritto).
- Abstract e indice con numeri di pagina romani, poi i capitoli numerati («Capitolo 1») e le
  appendici («Appendice A»).
- Citazioni numeriche [1, 2] nell'ordine di prima citazione. La bibliografia è la lista numerata della
  sezione «## Bibliografia» del Markdown (la voce n è la n-esima chiave citata, controllata sul primo
  autore in thesis/bibliografia.bib); se la sezione non ha una lista, le voci si generano dal .bib.
- Formule, figure con didascalia numerata, tabelle (booktabs, tabularx), elenchi, codice.

Uso, dalla radice del repository:
    .venv/Scripts/python.exe scripts/build_tesi_latex.py [--source thesis/ALTRA.md] [--tectonic PERCORSO] [--tex-only]

Con --source un altro file Markdown diventa thesis/latex/<nome>_unibo.tex e .pdf; se esiste
thesis/latex/frontespizio_<nome senza "tesi_">.tex il frontespizio è quello (TESI_kellybench.md usa
frontespizio_kellybench.tex).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THESIS = REPO / "thesis"
SOURCE = THESIS / "TESI.md"
BIB = THESIS / "bibliografia.bib"
OUT_DIR = THESIS / "latex"
TEX = OUT_DIR / "TESI_unibo.tex"
FRONT = OUT_DIR / "frontespizio.tex"
# sezioni (numero nel titolo Markdown) in cui ogni figura ha una pagina tutta per sé
FULL_PAGE_SECTIONS = {"5.4"}
# nome dei file finali da consegnare (PDF qui, .docx in build_tesi_docx.py), per sorgente Markdown
DELIVERABLE_NAMES = {"TESI_kellybench": "Malservigi_Tesi_KellyBench"}
# sezioni che cominciano su una pagina nuova
NEW_PAGE_SECTIONS = {"4.3", "7.2"}
DEFAULT_TECTONIC = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "tectonic" / "tectonic.exe"

FRONT_TEMPLATE = r"""% Dati del frontespizio: modificare qui, il file non viene sovrascritto.
\newcommand{\Dipartimento}{Dipartimento di \textcolor{red}{DA COMPLETARE}}
\newcommand{\CorsoDiLaurea}{Corso di Laurea in \textcolor{red}{DA COMPLETARE}}
\newcommand{\Titolo}{Dall'assenza di vantaggio alla supervisione del rischio}
\newcommand{\Sottotitolo}{Uno studio di conferma di KellyBench con importanti precisazioni}
\newcommand{\Insegnamento}{Tesi di Laurea in \textcolor{red}{DA COMPLETARE}}
\newcommand{\Relatore}{Prof.\\ Marco Roccetti}
\newcommand{\Candidato}{Federico Malservigi}
\newcommand{\Sessione}{Sessione \textcolor{red}{DA COMPLETARE}}
\newcommand{\AnnoAccademico}{Anno Accademico \textcolor{red}{DA COMPLETARE}}
"""

PREAMBLE = r"""\documentclass[11pt,a4paper,oneside]{report}
\usepackage{fontspec}
\usepackage[italian]{babel}
\usepackage[a4paper,top=3cm,bottom=3cm,left=3cm,right=3cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,tabularx,array,xltabular}
\usepackage{needspace}
\usepackage{etoolbox}
% nota introduttiva della bibliografia, subito sotto il titolo
\newcommand{\bibintro}{}
\patchcmd{\thebibliography}{\chapter*{\bibname}}{\chapter*{\bibname}\bibintro}{}{}
\usepackage[table]{xcolor}
\usepackage{caption}
\usepackage[hidelinks]{hyperref}
\graphicspath{{../}}
\captionsetup{font=small,labelfont=bf}
\renewcommand{\arraystretch}{1.2}
\setlength{\tabcolsep}{7pt}
\setlength{\parskip}{0.3em}
\setlength{\emergencystretch}{3em}
% ogni capitolo comincia su una pagina di destra (dispari nel fascicolo stampato): se serve, prima
% una pagina bianca senza numero. \ReadonlyShipoutCounter conta le pagine già uscite, frontespizio compreso
\newcommand{\paginabianca}{\clearpage\ifodd\ReadonlyShipoutCounter\thispagestyle{empty}\mbox{}\clearpage\fi}
\input{frontespizio}
\begin{document}

\hypersetup{pageanchor=false}
\begin{titlepage}
\centering
\includegraphics[width=3.2cm]{latex/sigillo_unibo.png}\par\vspace{0.5cm}
{\large\textsc{Alma Mater Studiorum $\cdot$ Università di Bologna}}\par\vspace{0.15cm}
\rule{\textwidth}{0.4pt}\par\vspace{0.4cm}
{\small\bfseries \Dipartimento\par \CorsoDiLaurea\par}
\vspace{2.2cm}
{\LARGE\bfseries \Titolo\par}\vspace{0.4cm}
{\Large\bfseries \Sottotitolo\par}
\vspace{1.8cm}
\if\relax\detokenize\expandafter{\Insegnamento}\relax\else{\small\bfseries \Insegnamento\par}\fi
\vfill
\begin{minipage}[t]{0.47\textwidth}\raggedright\bfseries Relatore:\\ \Relatore\end{minipage}\hfill
\begin{minipage}[t]{0.47\textwidth}\raggedleft\bfseries Presentata da:\\ \Candidato\end{minipage}\par
\vspace{1.2cm}
\rule{\textwidth}{1.2pt}\par\vspace{0.6cm}
{\bfseries \Sessione\par \AnnoAccademico\par}
\end{titlepage}
\hypersetup{pageanchor=true}

\pagenumbering{roman}
"""

SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape(text: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in text)


# ---------- bibliografia ----------
def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", path.read_text(encoding="utf-8"), re.S):
        fields = {"type": m.group(1).lower()}
        for f in re.finditer(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\},?\s*$", m.group(3), re.M):
            fields[f.group(1).lower()] = f.group(2).strip()
        entries[m.group(2).strip()] = fields
    return entries


def person(name: str) -> str:
    parts = [p.strip() for p in name.split(",")]
    if len(parts) == 1:
        return parts[0]
    last, first, *suffix = parts
    return " ".join([first, last] + suffix)


def ascii_letters(text: str) -> str:
    """Solo le lettere, senza accenti né comandi LaTeX: «K{\\"u}nsch» e «Künsch» diventano «kunsch»."""
    text = unicodedata.normalize("NFKD", re.sub(r"\\[a-zA-Z]+|\\.", "", text))
    return "".join(c for c in text.lower() if "a" <= c <= "z")


def first_surname(e: dict[str, str]) -> str:
    first = e.get("author", e.get("editor", "")).split(" and ")[0]
    return ascii_letters(first.split(",")[0] if "," in first else first.split()[-1])


def bib_item(key: str, e: dict[str, str]) -> str:
    names = [person(a) for a in e.get("author", e.get("editor", "")).split(" and ") if a.strip()]
    who = ", ".join(names[:-1]) + (" e " if len(names) > 1 else "") + (names[-1] if names else "")
    parts = [f"{who}, \\emph{{{e.get('title', '')}}}"]
    if "journal" in e:
        j = e["journal"]
        if "volume" in e:
            j += f", {e['volume']}" + (f"({e['number']})" if "number" in e else "")
        if "pages" in e:
            j += f", {e['pages']}"
        parts.append(j)
    elif "booktitle" in e:
        parts.append("in " + e["booktitle"] + (f", {e['pages']}" if "pages" in e else ""))
    for field in ("publisher", "institution", "howpublished"):
        if field in e:
            parts.append(e[field])
    parts.append(e.get("year", "s.d."))
    text = ", ".join(parts) + "."
    if "note" in e:
        text += " " + e["note"] + "."
    if "url" in e:
        text += f" Disponibile: \\url{{{e['url']}}}."
    return f"\\bibitem{{{key}}} {text}"


# ---------- testo in linea ----------
def inline(md: str, cited: list[str]) -> str:
    # formule e citazioni diventano segnaposto, così grassetto e corsivo possono contenerle
    kept: list[str] = []
    out = []
    for tok in re.split(r"(\$[^$]+\$|\[@[^\]]+\])", md):
        if not tok:
            continue
        if tok.startswith("$"):
            kept.append(tok)
        elif tok.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in tok[1:-1].split(";")]
            for k in keys:
                if k not in cited:
                    cited.append(k)
            kept.append(r"~\cite{" + ",".join(keys) + "}")
        else:
            out.append(escape(tok))
            continue
        out.append(f"\x00{len(kept) - 1}\x00")
    s = "".join(out)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
    text = re.sub("\x00(\\d+)\x00", lambda m: kept[int(m.group(1))], s)
    return re.sub(r"\s+~\\cite", r"~\\cite", text)


TEXT_WIDTH_PT = 425.0     # A4 con margini di 3 cm
TEXT_HEIGHT_PT = 672.0
TABCOLSEP_PT = 7.0
CHAR_PT = 4.9             # larghezza media di un carattere in \small
LINE_PT = 12.5            # altezza di una riga di testo in \small
NUMERIC = re.compile(r"(\*\*)?[−\-+]?[£$]?[\d.,]+\s*%?(\*\*)?|\$[^$]+\$|—|-")


def cell_size(s: str) -> int:
    return len(re.sub(r"\$[^$]*\$", "xx", re.sub(r"\*", "", s)))


def column_widths(rows: list[list[str]]) -> list[float]:
    """Frazioni di \\hsize per colonna (sommano al numero di colonne, come vuole tabularx)."""
    n = len(rows[0])
    body = rows[1:] or rows
    # peso: lunghezza media del testo della colonna (le colonne di testo lungo non schiacciano le altre),
    # l'intestazione conta al più 14 caratteri perché può andare a capo
    lens = [max(sum(cell_size(r[c]) for r in body) / len(body), min(cell_size(rows[0][c]), 14), 3) for c in range(n)]
    lens = [l ** 0.7 if l > 20 else l * 20 ** -0.3 for l in lens]
    # nessuna colonna più stretta della sua parola più lunga
    plain = lambda t: re.sub(r"\$[^$]*\$", "xxxxxx", t.replace("*", ""))  # noqa: E731  formula ~ 6 caratteri
    longest = [max((len(w) for r in rows for w in re.split(r"\s+", plain(r[c])) if w), default=3) for c in range(n)]
    sep = tabcolsep(n)
    min_frac = [n * (1.2 * w * CHAR_PT + 2 * sep) / TEXT_WIDTH_PT for w in longest]
    if sum(min_frac) >= n:  # non c'è spazio per tutte: si restringe tutto in proporzione
        return [n * m / sum(min_frac) for m in min_frac]
    # le colonne che in proporzione sarebbero troppo strette prendono il minimo, le altre si dividono il resto
    fixed: set[int] = set()
    while True:
        rest = n - sum(min_frac[i] for i in fixed)
        weight = sum(lens[i] for i in range(n) if i not in fixed)
        widths = [min_frac[i] if i in fixed else rest * lens[i] / weight for i in range(n)]
        short = {i for i in range(n) if i not in fixed and widths[i] < min_frac[i]}
        if not short:
            return widths
        fixed |= short


def tabcolsep(n: int) -> float:
    return TABCOLSEP_PT if n < 7 else 4.0


def column_spec(rows: list[list[str]], widths: list[float]) -> str:
    specs = []
    for c, w in enumerate(widths):
        numeric = all(NUMERIC.fullmatch(r[c].strip()) for r in rows[1:] if r[c].strip())
        align = r"\raggedleft" if numeric else r"\raggedright"
        specs.append(r">{%s\arraybackslash\hsize=%.3f\hsize}X" % (align, w))
    return "".join(specs)


def table_height(rows: list[list[str]], widths: list[float], gap: float) -> float:
    n = len(rows[0])
    chars = [max(w * TEXT_WIDTH_PT / n - 2 * tabcolsep(n), 10) / CHAR_PT for w in widths]
    lines = [max(-(-cell_size(r[c]) // int(chars[c])) or 1 for c in range(n)) for r in rows]
    return sum(lines) * LINE_PT + len(rows) * (3 + gap) + 20


def table(rows: list[list[str]], cited: list[str]) -> str:
    widths = column_widths(rows)
    spec = column_spec(rows, widths)
    header = " & ".join(r"\textbf{" + inline(c, cited) + "}" if c else "" for c in rows[0]) + r" \\"
    body = [" & ".join(inline(c, cited) for c in r) + r" \\" for r in rows[1:]]
    # le tabelle di testo (celle su più righe) hanno un filetto chiaro e un po' d'aria fra una riga e l'altra
    wordy = any(cell_size(c) > 45 for r in rows[1:] for c in r)
    gap = 9.0 if wordy else 0.0
    sep = r"\arrayrulecolor{black!20}\midrule[0.3pt]\arrayrulecolor{black}" if wordy else ""
    size = r"\small" if len(widths) < 7 else r"\footnotesize"
    size += r"\setlength{\tabcolsep}{%gpt}" % tabcolsep(len(widths))
    lines = [body[0]] if body else []
    for b in body[1:]:
        lines += ([sep] if sep else []) + [b]
    if table_height(rows, widths, gap) < 0.85 * TEXT_HEIGHT_PT:
        # tabella che sta in una pagina: un blocco unico, che non si spezza mai fra due pagine
        return "\n".join([r"\par\medskip\noindent\begin{minipage}{\textwidth}" + size,
                          r"\begin{tabularx}{\textwidth}{" + spec + "}", r"\toprule", header, r"\midrule",
                          *lines, r"\bottomrule", r"\end{tabularx}", r"\end{minipage}\par\medskip"])
    # tabella più alta di una pagina: xltabular (tabularx su longtable) va a capo fra due righe,
    # con l'intestazione ripetuta, e non comincia in fondo a una pagina con una riga sola
    return "\n".join([r"\needspace{0.45\textheight}\begingroup" + size, r"\begin{xltabular}{\textwidth}{" + spec + "}",
                      r"\toprule", header, r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot",
                      r"\bottomrule", r"\endlastfoot", *lines, r"\end{xltabular}", r"\endgroup"])


def is_portrait(png: Path) -> bool:
    """Vero se l'immagine PNG è più alta che larga (dimensioni lette dall'intestazione IHDR)."""
    try:
        head = png.read_bytes()[:24]
    except OSError:
        return False
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    width, height = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    return height > width


# ---------- blocchi ----------
def convert(md: str) -> tuple[str, list[str], list[str], str]:
    """Corpo LaTeX, chiavi citate in ordine di prima citazione, voci e nota della bibliografia del Markdown."""
    md_bib: list[str] = []
    md_bib_intro: list[str] = []
    lines = md.split("\n")
    out: list[str] = []
    cited: list[str] = []
    i = 0
    in_appendix = False
    full_page = False
    fig_pages = False  # siamo dentro un gruppo di figure a pagina intera
    # salta titolo e indice scritto a mano
    while not lines[i].startswith("## "):
        i += 1
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if fig_pages and not line.startswith("!["):
            # dopo il gruppo di figure a pagina intera il testo riparte su una pagina nuova
            out.append("\\clearpage")
            fig_pages = False
        if line.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append("{\\small\n\\begin{verbatim}\n" + "\n".join(lines[i + 1:j]) + "\n\\end{verbatim}\n}")
            i = j + 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if level <= 3:
                full_page = level == 3 and title.split(" ")[0] in FULL_PAGE_SECTIONS
            if level == 2:
                if title.startswith("0. "):
                    name = title[3:]
                    out.append(f"\\paginabianca\n\\chapter*{{{escape(name)}}}\n\\addcontentsline{{toc}}{{chapter}}{{{escape(name)}}}")
                elif title == "Appendici":
                    out.append("\\appendix")
                    in_appendix = True
                elif title == "Bibliografia":
                    out.append("%%BIBLIOGRAFIA%%")
                    # la lista numerata scritta nel Markdown è la bibliografia del PDF; il testo prima
                    # della lista è la nota introduttiva
                    i += 1
                    intro: list[str] = []
                    while i < len(lines) and not lines[i].startswith("## "):
                        item = re.match(r"^\d+\.\s+(.*)$", lines[i])
                        if item:
                            md_bib.append(item.group(1).strip())
                        elif lines[i].strip() and not md_bib:
                            intro.append(lines[i].strip())
                        i += 1
                    md_bib_intro.append(" ".join(intro))
                    continue
                else:
                    name = re.sub(r"^\d+\.\s*", "", title)
                    if name.startswith("Introduzione"):
                        out.append("\\paginabianca\n\\tableofcontents\n\\paginabianca\n\\pagenumbering{arabic}")
                    else:
                        out.append("\\paginabianca")
                    out.append(f"\\chapter{{{inline(name, cited)}}}")
            elif level == 3:
                if in_appendix:
                    name = re.sub(r"^Appendice [A-Z]\.\s*", "", title)
                    out.append("\\paginabianca")
                    out.append(f"\\chapter{{{inline(name, cited)}}}")
                else:
                    name = re.sub(r"^\d+\.\d+\s*", "", title)
                    if title.split(" ")[0] in NEW_PAGE_SECTIONS:
                        out.append("\\clearpage")
                    out.append(f"\\section{{{inline(name, cited)}}}")
            else:
                out.append(f"\\subsection*{{{inline(title, cited)}}}")
            i += 1
            continue
        if s == "$$":
            j = lines.index("$$", i + 1)
            body = "\n".join(lines[i + 1:j]).strip()
            out.append(f"\\begin{{equation*}}\n{body}\n\\end{{equation*}}")
            i = j + 1
            continue
        if line.startswith("!["):
            path = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line).group(1)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            caption = ""
            if j < len(lines) and lines[j].startswith("*Figura"):
                cap = lines[j].strip().strip("*")
                caption = re.sub(r"^Figura\s+[\dA-Z]+\.\d+\.\s*", "", cap)
                i = j + 1
            else:
                i += 1
            place, height = ("p", "0.8") if full_page else ("htbp", "0.42")
            if not full_page and is_portrait(THESIS / path):
                height = "0.7"  # una figura verticale con il limite di 0,42 resterebbe larga mezza pagina
            if full_page and not fig_pages:
                # il testo prima del gruppo di figure a pagina intera si chiude qui, così le pagine
                # di figure non finiscono in mezzo a una frase
                out.append("\\clearpage")
                fig_pages = True
            out.append(f"\\begin{{figure}}[{place}]\n\\centering\n"
                       f"\\includegraphics[width=\\textwidth,height={height}\\textheight,keepaspectratio]{{{path}}}\n"
                       f"\\caption{{{inline(caption, cited)}}}\n\\end{{figure}}")
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append(table(rows, cited))
            continue
        if re.match(r"^(- |\d+\. )", line):
            numbered = bool(re.match(r"^\d+\. ", line))
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                items.append("\\item " + inline(re.sub(r"^(- |\d+\. )", "", lines[i]), cited))
                i += 1
            env = "enumerate" if numbered else "itemize"
            out.append(f"\\begin{{{env}}}\n" + "\n".join(items) + f"\n\\end{{{env}}}")
            continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("\\begin{quote}\n" + inline(" ".join(quote), cited) + "\n\\end{quote}")
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"(#|\$\$|!\[|\||- |\d+\. |>|```)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(inline(" ".join(para), cited))
    return "\n\n".join(out), cited, md_bib, " ".join(md_bib_intro)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tectonic", default=str(DEFAULT_TECTONIC))
    ap.add_argument("--tex-only", action="store_true")
    ap.add_argument("--source", default=str(SOURCE))
    args = ap.parse_args()
    source = Path(args.source)
    tex = TEX if source.resolve() == SOURCE.resolve() else OUT_DIR / f"{source.stem}_unibo.tex"
    front_name = "frontespizio_" + source.stem.lower().replace("tesi_", "")
    front = front_name if (OUT_DIR / f"{front_name}.tex").exists() else "frontespizio"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not FRONT.exists():
        FRONT.write_text(FRONT_TEMPLATE, encoding="utf-8")
    body, cited, md_bib, md_bib_intro = convert(source.read_text(encoding="utf-8"))
    bib = parse_bib(BIB)
    missing = [k for k in cited if k not in bib]
    if missing:
        raise SystemExit(f"Citazioni senza voce in bibliografia: {missing}")
    if md_bib:
        # bibliografia scritta nel Markdown: la voce n è la n-esima chiave citata; il .bib serve da controllo
        if len(md_bib) != len(cited):
            raise SystemExit(f"La bibliografia del Markdown ha {len(md_bib)} voci, le citazioni sono {len(cited)}")
        wrong = [f"{n}. {k}" for n, (k, text) in enumerate(zip(cited, md_bib), 1)
                 if first_surname(bib[k]) not in ascii_letters(text)]
        if wrong:
            raise SystemExit(f"Voci del Markdown che non corrispondono alla citazione: {wrong}")
        items = [f"\\bibitem{{{k}}} {inline(text, [])}" for k, text in zip(cited, md_bib)]
    else:
        items = [bib_item(k, bib[k]) for k in cited]
    intro = f"\\renewcommand{{\\bibintro}}{{{inline(md_bib_intro, [])}\\par\\medskip}}\n" if md_bib_intro else ""
    bibliography = ("\\paginabianca\n" + intro + "\\begin{thebibliography}{99}\n"
                    "\\addcontentsline{toc}{chapter}{Bibliografia}\n\\raggedright\n"
                    + "\n".join(items) + "\n\\end{thebibliography}")
    body = body.replace("%%BIBLIOGRAFIA%%", bibliography)
    if (OUT_DIR / "ringraziamenti.tex").exists():
        # nei ringraziamenti nessuna parola va a capo con il trattino
        body += ("\n\n\\paginabianca\n\\chapter*{Ringraziamenti}\n\\addcontentsline{toc}{chapter}{Ringraziamenti}\n"
                 "\\begingroup\\hyphenpenalty=10000\\exhyphenpenalty=10000\n\\input{ringraziamenti}\n\\par\\endgroup")
    preamble = PREAMBLE.replace("\\input{frontespizio}", "\\input{" + front + "}")
    tex.write_text(preamble + body + "\n\n\\end{document}\n", encoding="utf-8")
    print("TEX:", tex)
    if args.tex_only:
        return
    tectonic = args.tectonic if Path(args.tectonic).exists() else shutil.which("tectonic")
    if not tectonic:
        raise SystemExit("Tectonic non trovato: passare --tectonic PERCORSO")
    subprocess.run([str(tectonic), "--keep-logs", tex.name], cwd=OUT_DIR, check=True)
    print("PDF:", tex.with_suffix(".pdf"))
    if source.stem in DELIVERABLE_NAMES:  # copia da allegare, con il nome definitivo
        final = THESIS / f"{DELIVERABLE_NAMES[source.stem]}.pdf"
        shutil.copyfile(tex.with_suffix(".pdf"), final)
        print("PDF:", final)


if __name__ == "__main__":
    main()
