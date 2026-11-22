"""Genera la tesi in LaTeX con il frontespizio dell'Università di Bologna, e la compila con Tectonic.

thesis/TESI.md -> thesis/latex/TESI_unibo.tex -> thesis/latex/TESI_unibo.pdf

- Frontespizio come nelle tesi Unibo (sigillo, dipartimento, corso, titolo, relatore, candidato,
  sessione, anno accademico); i dati sono in thesis/latex/frontespizio.tex, creato al primo
  avvio con dei segnaposto e poi mai sovrascritto.
- Ringraziamenti in fondo, se esiste thesis/latex/ringraziamenti.tex (mai sovrascritto).
- Abstract e indice con numeri di pagina romani, poi i capitoli numerati («Capitolo 1») e le
  appendici («Appendice A»).
- Citazioni numeriche [1, 2] nell'ordine di prima citazione, bibliografia da thesis/bibliografia.bib
  (solo le voci citate).
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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THESIS = REPO / "thesis"
SOURCE = THESIS / "TESI.md"
BIB = THESIS / "bibliografia.bib"
OUT_DIR = THESIS / "latex"
TEX = OUT_DIR / "TESI_unibo.tex"
FRONT = OUT_DIR / "frontespizio.tex"
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
\usepackage{xcolor}
\usepackage{caption}
\usepackage[hidelinks]{hyperref}
\graphicspath{{../}}
\captionsetup{font=small,labelfont=bf}
\renewcommand{\arraystretch}{1.15}
\setlength{\parskip}{0.3em}
\setlength{\emergencystretch}{3em}
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
    out = []
    for tok in re.split(r"(\$[^$]+\$|\[@[^\]]+\])", md):
        if not tok:
            continue
        if tok.startswith("$"):
            out.append(tok)
        elif tok.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in tok[1:-1].split(";")]
            for k in keys:
                if k not in cited:
                    cited.append(k)
            out.append(r"~\cite{" + ",".join(keys) + "}")
        else:
            s = escape(tok)
            s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
            s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
            out.append(s)
    text = "".join(out)
    return re.sub(r"\s+~\\cite", r"~\\cite", text)


def column_spec(rows: list[list[str]]) -> str:
    n = len(rows[0])
    size = lambda s: len(re.sub(r"\$[^$]*\$", "xx", re.sub(r"\*", "", s)))  # noqa: E731
    # le intestazioni possono andare a capo: pesano al più 14 caratteri
    lens = [max(max((size(r[c]) for r in rows[1:]), default=0), min(size(rows[0][c]), 14), 3) for c in range(n)]
    lens = [min(l, 60) for l in lens]
    # nessuna colonna più stretta della sua parola più lunga
    longest = [max(len(w) for r in rows for w in re.split(r"\s+", r[c]) if w) for c in range(n)]
    lens = [max(l, int(1.4 * w)) for l, w in zip(lens, longest)]
    total = sum(lens)
    widths = [n * l / total for l in lens]
    return "".join(r">{\raggedright\arraybackslash\hsize=%.3f\hsize}X" % w for w in widths)


def table(rows: list[list[str]], cited: list[str]) -> str:
    body = [" & ".join(inline(c, cited) for c in r) + r" \\" for r in rows]
    # xltabular (tabularx su longtable): una tabella più alta di una pagina va a capo, con l'intestazione ripetuta
    return "\n".join([r"\begingroup\small", r"\begin{xltabular}{\textwidth}{" + column_spec(rows) + "}",
                      r"\toprule", body[0], r"\midrule", r"\endhead", *body[1:], r"\bottomrule", r"\end{xltabular}",
                      r"\endgroup"])


# ---------- blocchi ----------
def convert(md: str) -> tuple[str, list[str]]:
    lines = md.split("\n")
    out: list[str] = []
    cited: list[str] = []
    i = 0
    in_appendix = False
    # salta titolo e indice scritto a mano
    while not lines[i].startswith("## "):
        i += 1
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
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
            if level == 2:
                if title.startswith("0. "):
                    name = title[3:]
                    out.append(f"\\chapter*{{{escape(name)}}}\n\\addcontentsline{{toc}}{{chapter}}{{{escape(name)}}}")
                elif title == "Appendici":
                    out.append("\\appendix")
                    in_appendix = True
                elif title == "Bibliografia":
                    out.append("%%BIBLIOGRAFIA%%")
                else:
                    name = re.sub(r"^\d+\.\s*", "", title)
                    if name.startswith("Introduzione"):
                        out.append("\\tableofcontents\n\\clearpage\n\\pagenumbering{arabic}")
                    out.append(f"\\chapter{{{inline(name, cited)}}}")
            elif level == 3:
                if in_appendix:
                    name = re.sub(r"^Appendice [A-Z]\.\s*", "", title)
                    out.append(f"\\chapter{{{inline(name, cited)}}}")
                else:
                    name = re.sub(r"^\d+\.\d+\s*", "", title)
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
            out.append("\\begin{figure}[htbp]\n\\centering\n"
                       f"\\includegraphics[width=\\textwidth,height=0.42\\textheight,keepaspectratio]{{{path}}}\n"
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
    return "\n\n".join(out), cited


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
    body, cited = convert(source.read_text(encoding="utf-8"))
    bib = parse_bib(BIB)
    missing = [k for k in cited if k not in bib]
    if missing:
        raise SystemExit(f"Citazioni senza voce in bibliografia: {missing}")
    bibliography = ("\\begin{thebibliography}{99}\n\\addcontentsline{toc}{chapter}{Bibliografia}\n"
                    + "\n".join(bib_item(k, bib[k]) for k in cited) + "\n\\end{thebibliography}")
    body = body.replace("%%BIBLIOGRAFIA%%", bibliography)
    if (OUT_DIR / "ringraziamenti.tex").exists():
        body += ("\n\n\\chapter*{Ringraziamenti}\n\\addcontentsline{toc}{chapter}{Ringraziamenti}\n"
                 "\\input{ringraziamenti}")
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


if __name__ == "__main__":
    main()
