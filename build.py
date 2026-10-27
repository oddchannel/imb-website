#!/usr/bin/env python3
"""Build the Institute for Mind and Biology website.

    python build.py            # build the site into _site/
    python build.py --serve    # build, then preview at http://localhost:8000

You normally never need to edit this file. Content lives in:
    site.yml      site title, menu, contact details
    data/*.yml    people, events, research areas, home-page highlights
    content/*.md  page text (Markdown)
"""
import argparse
import datetime as dt
import http.server
import re
import shutil
import sys
from pathlib import Path

import jinja2
import markdown as md
import yaml
from markupsafe import Markup

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
problems = []


def load_yaml(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    except yaml.YAMLError as e:
        sys.exit(f"\nERROR: {path.relative_to(ROOT)} is not valid YAML.\n{e}\n"
                 "Check indentation (use spaces, not tabs) and that text containing ':' is in quotes.")


def render_md(text):
    return md.markdown(text or "", extensions=["extra", "smarty"])


def read_page(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if not m:
        sys.exit(f"\nERROR: {path.relative_to(ROOT)} must start with a '---' header block.")
    meta = yaml.safe_load(m.group(1)) or {}
    meta["content"] = Markup(render_md(m.group(2)))
    meta.setdefault("layout", "page")
    meta.setdefault("url", f"/{path.stem}/")
    return meta


def check(cond, msg):
    if not cond:
        problems.append(msg)


def validate(data):
    area_ids = {a["id"] for a in data["research_areas"]}
    for group in ("faculty", "fellows", "staff"):
        for p in data[group]:
            who = f"data/{group}.yml: {p.get('name', '(no name)')}"
            check(p.get("name"), f"{who} is missing a name")
            photo = p.get("photo")
            check(not photo or (ROOT / "static" / photo.lstrip("/")).exists(),
                  f"{who}: photo file not found: static{photo}")
    for p in data["faculty"]:
        for a in p.get("areas") or []:
            check(a in area_ids, f"data/faculty.yml: {p['name']} has unknown area '{a}' "
                                 f"(valid: {', '.join(sorted(area_ids))})")
    for e in data["events"]:
        if isinstance(e.get("date"), str):  # e.g. "2025-01-31" saved in quotes
            try:
                e["date"] = dt.date.fromisoformat(e["date"].strip()[:10])
            except ValueError:
                pass
        check(isinstance(e.get("date"), dt.date),
              f"data/events.yml: '{e.get('title')}' needs a date like 2025-01-31 (got {e.get('date')!r})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="preview the site locally")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--base-path", default="",
                    help="URL prefix if the site is not at the domain root, e.g. /imb-website")
    args = ap.parse_args()
    base = args.base_path.rstrip("/")

    site = load_yaml(ROOT / "site.yml")
    data = {p.stem: load_yaml(p) for p in sorted((ROOT / "data").glob("*.yml"))}
    validate(data)
    if problems:
        sys.exit("\nPlease fix these problems:\n  - " + "\n  - ".join(problems) + "\n")

    today = dt.date.today()
    events = sorted(data["events"], key=lambda e: e["date"])
    data["upcoming_events"] = [e for e in events if e["date"] >= today]
    data["past_events"] = list(reversed([e for e in events if e["date"] < today]))
    for area in data["research_areas"]:
        area["members"] = [p for p in data["faculty"] if area["id"] in (p.get("areas") or [])]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT / "templates"),
                             autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["markdown"] = lambda s: Markup(render_md(s))
    env.filters["longdate"] = lambda d: f"{d:%A, %B} {d.day}, {d.year}"

    pages = [read_page(p) for p in sorted((ROOT / "content").glob("*.md"))]
    for area in data["research_areas"]:
        pages.append({"title": area["name"], "layout": "area", "area": area, "content": "",
                      "url": f"/research/{area['id']}/", "aliases": area.get("aliases", [])})

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)

    def write(url, html):
        if base:  # prefix root-relative links when hosted in a sub-folder
            html = re.sub(r"""(href="|src="|url=|url\(')/(?!/)""", rf"\1{base}/", html)
        dest = OUT / url.lstrip("/")
        if not url.endswith(".html"):
            dest = dest / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    for page in pages:
        tpl = env.get_template(f"{page['layout']}.html")
        write(page["url"], tpl.render(site=site, data=data, page=page, today=today))
        for old in page.get("aliases") or []:
            write(old, env.get_template("redirect.html").render(target=page["url"]))
    print(f"Built {len(pages)} pages into {OUT.relative_to(ROOT)}/")

    if args.serve:
        handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=OUT, **kw)
        print(f"Preview at http://localhost:{args.port}  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
