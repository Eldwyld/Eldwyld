#!/usr/bin/env python3
"""Build SpiralSighted Marks: sticker sheet PDFs (Letter + A4),
per-sticker transparent PNGs, and QA page renders."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"
CHROME = "/opt/pw-browsers/chromium"

EDITIONS = {
    "letter": {"size": "8.5in 11in", "w": "8.5in", "h": "11in"},
    "a4":     {"size": "210mm 297mm", "w": "210mm", "h": "297mm"},
}

# sticker id → (viewBox, png width)
STICKERS = {
    "st-moon":     ("-14 -14 232 240", 900),
    "st-fullmoon": ("-14 -14 234 234", 900),
    "st-star":     ("-14 -14 232 246", 900),
    "st-sigil":    ("-14 -14 234 234", 900),
    "st-banner":   ("-16 -20 348 168", 1200),
    "st-glitch":   ("-14 -16 232 210", 900),
    "st-crystal":  ("-14 -14 232 232", 900),
    "st-frog":     ("-14 -18 232 232", 900),
    "st-shrooms":  ("-14 -14 232 232", 900),
    "st-potion":   ("-14 -16 230 236", 900),
    "st-candle":   ("-14 -16 230 236", 900),
    "st-debris":   ("-14 -14 232 216", 900),
}

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>SpiralSighted Marks — Sigils &amp; Specimens</title>
<link rel="stylesheet" href="../src/fonts/fonts-local.css">
<style>{css}</style>
</head><body>
"""


def chrome(*args):
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--hide-scrollbars", "--force-color-profile=srgb",
         "--allow-file-access-from-files", "--virtual-time-budget=12000",
         *args],
        check=True, capture_output=True)


def assemble(edition):
    spec = EDITIONS[edition]
    css = (SRC / "marks.css").read_text()
    css = (css.replace("__PAGE_SIZE__", spec["size"])
              .replace("__PAGE_W__", spec["w"]).replace("__PAGE_H__", spec["h"]))
    body = (SRC / "stickers-defs.html").read_text() + (SRC / "sheets.html").read_text()
    out = DIST / f"sheets-{edition}.html"
    out.write_text(HEAD.format(css=css) + body + "</body></html>\n")
    return out


def render_pdfs():
    for ed in EDITIONS:
        html = assemble(ed)
        pdf = DIST / f"SpiralSighted-Marks-{'A4' if ed == 'a4' else 'Letter'}.pdf"
        chrome(f"--print-to-pdf={pdf}", "--no-pdf-header-footer", html.as_uri())
        print(f"  ✓ {pdf.name} ({pdf.stat().st_size // 1024} KB)")


def render_pngs():
    outdir = DIST / "png"
    outdir.mkdir(exist_ok=True)
    defs = (SRC / "stickers-defs.html").read_text()
    for sid, (vb, w) in STICKERS.items():
        x, y, vw, vh = (float(v) for v in vb.split())
        h = round(w * vh / vw)
        one = DIST / "_one.html"
        one.write_text(
            f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../src/fonts/fonts-local.css">
<style>*{{margin:0;padding:0}}html,body{{background:transparent}}</style></head>
<body>{defs}<svg viewBox="{vb}" width="{w}" height="{h}"><use href="#{sid}"/></svg>
</body></html>""")
        png = outdir / f"{sid[3:]}.png"
        chrome(f"--screenshot={png}", f"--window-size={w},{h}",
               "--default-background-color=00000000", one.as_uri())
        print(f"  ✓ {png.name}")
    (DIST / "_one.html").unlink(missing_ok=True)


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "--png-only":
        render_pdfs()
    if mode != "--pdf-only":
        render_pngs()
