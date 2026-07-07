#!/usr/bin/env python3
"""Build The Forager's Grimoire: assemble HTML, render PDFs (Letter + A4)
and per-page PNG previews with headless Chromium.

Usage: python3 build.py [--pdf-only | --png-only]
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"
CHROME = "/opt/pw-browsers/chromium"

EDITIONS = {
    "letter": {"size": "8.5in 11in", "w": "8.5in", "h": "11in"},
    "a4":     {"size": "210mm 297mm", "w": "210mm", "h": "297mm"},
}

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>The Forager's Grimoire — The Eldwyld Archives</title>
<link rel="stylesheet" href="../src/fonts/fonts-local.css">
<style>{css}</style>
</head><body>
"""
FOOT = "</body></html>\n"


def assemble(edition: str) -> Path:
    spec = EDITIONS[edition]
    css = (SRC / "style.css").read_text()
    css = (css.replace("__PAGE_SIZE__", spec["size"])
              .replace("__PAGE_W__", spec["w"])
              .replace("__PAGE_H__", spec["h"]))
    body = "".join((SRC / f).read_text()
                   for f in ["defs.html", "pages-1.html", "pages-2.html", "pages-3.html"])
    out = DIST / f"grimoire-{edition}.html"
    out.write_text(HEAD.format(css=css) + body + FOOT)
    return out


def chrome(*args):
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--hide-scrollbars", "--force-color-profile=srgb",
         "--allow-file-access-from-files", "--virtual-time-budget=10000",
         *args],
        check=True, capture_output=True)


def render_pdf(edition: str):
    html = assemble(edition)
    pdf = DIST / f"The-Foragers-Grimoire-{edition.upper() if edition == 'a4' else edition.capitalize()}.pdf"
    chrome(f"--print-to-pdf={pdf}", "--no-pdf-header-footer", html.as_uri())
    print(f"  ✓ {pdf.name} ({pdf.stat().st_size // 1024} KB)")


def render_pngs(pages: list[int] | None = None, scale: float = 2.0):
    """Rasterize Letter-edition PDF pages to PNG (source of truth for previews)."""
    import pypdfium2 as pdfium
    pdf_path = DIST / "The-Foragers-Grimoire-Letter.pdf"
    if not pdf_path.exists():
        render_pdf("letter")
    doc = pdfium.PdfDocument(pdf_path)
    outdir = DIST / "pages"
    outdir.mkdir(exist_ok=True)
    for i in (pages or range(1, len(doc) + 1)):
        png = outdir / f"page-{i:02d}.png"
        doc[i - 1].render(scale=scale).to_pil().save(png)
        print(f"  ✓ {png.name}")


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "--png-only":
        for ed in EDITIONS:
            render_pdf(ed)
    if mode != "--pdf-only":
        args = [int(a) for a in sys.argv[2:]] if len(sys.argv) > 2 else None
        render_pngs(args)
