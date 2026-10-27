#!/usr/bin/env python3
"""Turn EDITING-GUIDE.md into a printable PDF using Google Chrome.

    python tools/make_guide_pdf.py                       # writes ../IMB-Website-Editing-Guide.pdf
    python tools/make_guide_pdf.py --out guide.pdf

Requires Google Chrome (macOS path by default; pass --chrome for others).
"""
import argparse
import pathlib
import re
import subprocess
import tempfile

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: letter; margin: 0.8in 0.85in 0.85in;
  @bottom-left { content: "IMB website editing guide"; font: 8.5pt Helvetica, Arial, sans-serif; color: #888; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font: 8.5pt Helvetica, Arial, sans-serif; color: #888; } }
@page :first { margin-top: 0.6in; }
body { font: 10.5pt/1.5 Helvetica, Arial, sans-serif; color: #1f1f1f; }
.cover { border-bottom: 3px solid #800000; padding-bottom: 14pt; margin-bottom: 18pt; }
.cover img { height: 34pt; }
h1 { font: 600 26pt/1.15 Georgia, serif; color: #800000; margin: 16pt 0 4pt; }
.lede { font-size: 12pt; color: #444; margin: 0; }
h2 { font: 600 16pt/1.2 Georgia, serif; color: #800000; border-bottom: 1.5px solid #800000;
     padding-bottom: 3pt; margin: 22pt 0 9pt; break-after: avoid; }
h3 { font: 600 12.5pt/1.25 Georgia, serif; margin: 14pt 0 5pt; break-after: avoid; }
.task { break-inside: avoid; background: #f8f6f3; border-left: 3px solid #800000;
        padding: 2pt 12pt 6pt; margin: 10pt 0; border-radius: 3pt; }
.task h3 { margin-top: 8pt; }
p { margin: 0 0 7pt; }
ol, ul { margin: 0 0 7pt; padding-left: 20pt; }
li { margin-bottom: 3pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; break-inside: avoid; font-size: 10pt; }
th { background: #800000; color: #fff; text-align: left; padding: 5pt 7pt; }
td { border-bottom: 1px solid #ddd; padding: 5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #faf9f7; }
code { font: 9.5pt Menlo, monospace; background: #eee; padding: 0 3pt; border-radius: 2pt; }
a { color: #800000; text-decoration: none; }
h2 + p { break-after: avoid; }
.blank { display: inline-block; width: 2.2in; border-bottom: 1px solid #333; }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "EDITING-GUIDE.md")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT.parent / "IMB-Website-Editing-Guide.pdf")
    ap.add_argument("--chrome", default=CHROME)
    args = ap.parse_args()

    text = args.src.read_text(encoding="utf-8")
    title = re.match(r"# (.+)\n", text).group(1)
    text = text[text.index("\n") + 1:].replace("**______________________**", "BLANKLINE")
    body = markdown.markdown(text, extensions=["extra", "smarty"]).replace("<hr />", "")
    # Keep each task (h3 and its steps) together on one page where possible.
    body = re.sub(r"(<h3>.*?)(?=<h3>|<h2>|$)", r'<section class="task">\1</section>', body, flags=re.S)
    body = body.replace("BLANKLINE", '<span class="blank"></span>')
    logo = (ROOT / "static/images/site/logo-color.png").as_uri()
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style>'
            f'</head><body><div class="cover"><img src="{logo}" alt=""><h1>{title}</h1>'
            f'<p class="lede">A step-by-step guide for the Institute for Mind and Biology website</p></div>'
            f"{body}</body></html>")

    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "guide.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([args.chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={tmp}/profile", f"--print-to-pdf={args.out.resolve()}",
                        page.as_uri()], check=True, capture_output=True)
    print("Wrote", args.out.resolve())


if __name__ == "__main__":
    main()
