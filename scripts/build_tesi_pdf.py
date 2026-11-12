"""Genera thesis/TESI.pdf da thesis/TESI.md, senza Pandoc né LaTeX.

Markdown -> HTML (con le formule rese da MathJax e le citazioni [@chiave] risolte
da thesis/bibliografia.bib) -> PDF stampato da Chrome o Edge in modalità headless.

Richiede i pacchetti `markdown` e `pymdown-extensions` (non sono dipendenze del
progetto: si possono installare in una cartella a parte e passarla con --pylib)
e un Chrome o un Edge installato. MathJax è caricato dalla rete.

    .venv/Scripts/python.exe scripts/build_tesi_pdf.py --pylib <cartella>
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THESIS = REPO / "thesis"
SOURCE = THESIS / "TESI.md"
BIB = THESIS / "bibliografia.bib"
HTML_OUT = REPO / "build" / "tesi" / "TESI.html"
PDF_OUT = THESIS / "TESI.pdf"

BROWSERS = [
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
]

LATEX_ACCENTS = {r"{\"u}": "ü", r"{\'e}": "é", r"\&": "&", "--": "–"}

CSS = """
@page { size: A4; margin: 2.5cm 2.3cm 2.5cm 2.3cm; }
body { font-family: 'Cambria', 'Georgia', serif; font-size: 11.5pt; line-height: 1.5; color: #111; }
h1 { font-size: 22pt; text-align: center; margin: 5cm 0 1cm 0; line-height: 1.25; }
.autore { text-align: center; font-size: 13pt; margin-bottom: 6cm; }
h2 { font-size: 17pt; page-break-before: always; margin-top: 0; }
h3 { font-size: 13.5pt; margin-top: 1.4em; }
h4 { font-size: 11.5pt; font-style: italic; margin-top: 1.2em; }
p { text-align: justify; margin: 0.5em 0; }
img { display: block; max-width: 100%; margin: 1em auto 0.3em auto; page-break-inside: avoid; }
table { border-collapse: collapse; margin: 0.8em auto; font-size: 9pt; page-break-inside: avoid; }
th, td { border-top: 1px solid #999; border-bottom: 1px solid #999; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
blockquote { margin: 1em 2em; font-size: 12pt; }
code, pre { font-family: Consolas, monospace; font-size: 9pt; }
pre { background: #f5f5f5; padding: 0.6em; }
.toc ul { list-style: none; padding-left: 1.2em; }
.toc > ul { padding-left: 0; }
.toc a { color: #111; text-decoration: none; }
.bibliografia p { text-align: left; padding-left: 2em; text-indent: -2em; }
p > em:only-child { display: block; font-size: 10pt; }
"""


def clean(text: str) -> str:
    for k, v in LATEX_ACCENTS.items():
        text = text.replace(k, v)
    return text.replace("{", "").replace("}", "").strip()


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", path.read_text(encoding="utf-8"), re.S):
        fields = {"type": m.group(1).lower()}
        for f in re.finditer(r"(\w+)\s*=\s*\{(.*?)\},?\s*$", m.group(3), re.M):
            fields[f.group(1).lower()] = clean(f.group(2))
        entries[m.group(2).strip()] = fields
    return entries


def surnames(authors: str) -> list[str]:
    return [a.split(",")[0].strip() for a in authors.split(" and ")]


def short_cite(e: dict[str, str]) -> str:
    s = surnames(e.get("author", e.get("editor", "?")))
    who = s[0] if len(s) == 1 else f"{s[0]} e {s[1]}" if len(s) == 2 else f"{s[0]} et al."
    return f"{who}, {e.get('year', 's.d.')}"


def full_ref(e: dict[str, str]) -> str:
    s = surnames(e.get("author", e.get("editor", "?")))
    names = ", ".join(s[:-1]) + (" e " if len(s) > 1 else "") + s[-1]
    parts = [f"{names} ({e.get('year', 's.d.')}). {e.get('title', '')}."]
    if "journal" in e:
        j = f"*{e['journal']}*"
        if "volume" in e:
            j += f", {e['volume']}"
            if "number" in e:
                j += f"({e['number']})"
        if "pages" in e:
            j += f", {e['pages']}"
        parts.append(j + ".")
    elif "booktitle" in e:
        parts.append(f"In *{e['booktitle']}*" + (f", {e['pages']}" if "pages" in e else "") + ".")
    if "publisher" in e:
        parts.append(e["publisher"] + ".")
    if "institution" in e:
        parts.append(e["institution"] + ".")
    if "note" in e:
        parts.append(e["note"] + ".")
    return " ".join(parts)


def resolve_citations(md: str, bib: dict) -> tuple[str, list[str]]:
    used: list[str] = []

    def repl(m: re.Match) -> str:
        keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        out = []
        for k in keys:
            if k not in bib:
                out.append(f"??{k}??")
                continue
            if k not in used:
                used.append(k)
            out.append(short_cite(bib[k]))
        return "(" + "; ".join(out) + ")"

    return re.sub(r"\[(@[^\]]+)\]", repl, md), used


def build_markdown(bib: dict) -> str:
    md = SOURCE.read_text(encoding="utf-8")
    title, _, rest = md.partition("\n")
    # l'indice scritto a mano diventa l'indice generato
    rest = re.sub(r"INDICE:\n(?:- .*\n)+", "## Indice\n\n[TOC]\n", rest, count=1)
    rest = rest.replace("**Abstract**", "## Abstract", 1)
    rest, used = resolve_citations(rest, bib)
    refs = sorted(used, key=lambda k: (surnames(bib[k].get("author", "?"))[0], bib[k].get("year", "")))
    bib_md = "\n\n".join(full_ref(bib[k]) for k in refs)
    rest = rest.replace("## Bibliografia", f"## Bibliografia\n\n<div class=\"bibliografia\" markdown=\"1\">\n\n{bib_md}\n\n</div>", 1)
    return title.lstrip("# ").strip(), rest


def to_html(title: str, body_md: str) -> str:
    import markdown

    body = markdown.markdown(
        body_md,
        extensions=["tables", "toc", "md_in_html", "fenced_code", "pymdownx.arithmatex"],
        extension_configs={"pymdownx.arithmatex": {"generic": True},
                           "toc": {"toc_depth": "2-3", "title": ""}},
    )
    mathjax = """
<script>
window.MathJax = { tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']], tags: 'none' },
                   svg: { fontCache: 'global' } };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script>"""
    base = THESIS.as_uri() + "/"
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<base href="{base}"><title>{html.escape(title)}</title><style>{CSS}</style>{mathjax}</head>
<body><h1>{html.escape(title)}</h1><div class="autore">Federico Malservigi</div>
{body}</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pylib", help="cartella con i pacchetti markdown e pymdown-extensions")
    ap.add_argument("--html-only", action="store_true")
    args = ap.parse_args()
    if args.pylib:
        sys.path.insert(0, args.pylib)

    bib = parse_bib(BIB)
    title, body_md = build_markdown(bib)
    missing = sorted(set(re.findall(r"\?\?(\w+)\?\?", body_md)))
    if missing:
        print("Citazioni senza voce in bibliografia:", ", ".join(missing))
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(to_html(title, body_md), encoding="utf-8")
    print("HTML:", HTML_OUT)
    if args.html_only:
        return

    browser = next((b for b in BROWSERS if b.exists()), None) or shutil.which("chrome") or shutil.which("msedge")
    if not browser:
        sys.exit("Nessun Chrome o Edge trovato.")
    subprocess.run([str(browser), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", "--virtual-time-budget=30000",
                    f"--print-to-pdf={PDF_OUT}", HTML_OUT.as_uri()], check=True, timeout=180)
    print("PDF:", PDF_OUT)


if __name__ == "__main__":
    main()
