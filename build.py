#!/usr/bin/env python3
"""Build the Institute for Mind and Biology website.

    python build.py            # build the site into _site/
    python build.py --serve    # build, then preview at http://localhost:8000
    python build.py --offline --out ../IMB-website-demo   # copy that opens from disk

You normally never need to edit this file. Content lives in:
    site.yml           site title, address, contact email
    menu.yml           navigation menu and footer links
    redirects.yml      old web addresses that should forward to new pages
    content/*.md       page text (Markdown)
    content/faculty/   one file per faculty member
    content/research/  one file per research area
    content/news/      one file per news post
    data/*.yml         fellows, staff, events, publications
"""
import argparse
import concurrent.futures
import datetime as dt
import html
import http.server
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

import jinja2
import markdown as md
import yaml
from markupsafe import Markup

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
CROSSREF_CACHE = ROOT / ".cache" / "crossref.json"
CHICAGO = ZoneInfo("America/Chicago")
# Templates that are building blocks, not page layouts.
NOT_LAYOUTS = {"base", "page", "redirect", "area", "news_post", "status"}
warnings = []


# ---------- reading content ----------

def load_yaml(path, default):
    if not path.exists():
        return default
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or default
    except yaml.YAMLError as e:
        sys.exit(f"\nERROR: {path.relative_to(ROOT)} is not valid YAML.\n{e}\n"
                 "Check indentation (use spaces, not tabs) and that text containing ':' is in quotes.")


def render_md(text):
    return Markup(md.markdown(text or "", extensions=["extra", "smarty"]))


def plain_excerpt(rendered, words=40):
    text = html.unescape(re.sub(r"<[^>]+>", " ", rendered))
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def read_md(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    meta, body = {}, raw
    if m:
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            sys.exit(f"\nERROR: the header of {path.relative_to(ROOT)} is not valid YAML.\n{e}")
        body = m.group(2)
    meta["slug"] = path.stem
    meta["content"] = render_md(body)
    return meta


def to_date(value, where):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        warnings.append(f"{where}: date should look like 2025-01-31 (got {value!r}); skipped")
        return None


def sort_key(person):
    words = re.sub(r"\(.*?\)", "", person.get("name") or "").split()
    return ((words[-1] if words else "").lower(), (person.get("name") or "").lower())


def check_photo(person, where):
    photo = person.get("photo")
    if photo and not (ROOT / "static" / photo.lstrip("/")).exists():
        warnings.append(f"{where}: photo not found ({photo}); showing initials instead")
        person["photo"] = ""


# ---------- publications (DOI lookup) ----------

def clean(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def format_authors(authors):
    names = []
    for a in authors:
        if "family" in a:
            initials = " ".join(p[0] + "." for p in (a.get("given") or "").split() if p)
            names.append(f"{a['family']}, {initials}".strip(", "))
        elif a.get("name"):
            names.append(a["name"])
    if len(names) > 10:
        return ", ".join(names[:10]) + ", et al."
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + ", & " + names[-1]


def crossref_lookup(dois):
    """Fetch title/authors/journal/year for each DOI from Crossref, remembering results."""
    cache = json.loads(CROSSREF_CACHE.read_text()) if CROSSREF_CACHE.exists() else {}
    missing = [d for d in dois if d not in cache]

    def fetch(doi):
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
        req = urllib.request.Request(url, headers={"User-Agent": "IMB-website (https://imb.uchicago.edu)"})
        for attempt in range(4):  # Crossref sometimes asks us to slow down; retry politely
            try:
                m = json.load(urllib.request.urlopen(req, timeout=20))["message"]
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return doi, None
            except Exception:
                pass
            time.sleep(2 ** attempt)
        else:
            return doi, None
        issued = (m.get("issued") or m.get("published") or {}).get("date-parts") or [[None]]
        return doi, {"title": clean(m.get("title")), "journal": clean(m.get("container-title")),
                     "year": issued[0][0], "authors": format_authors(m.get("author") or [])}

    if missing:
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            for doi, info in pool.map(fetch, missing):
                if info:
                    cache[doi] = info
                else:
                    warnings.append(f"Publications: couldn't look up DOI {doi}; "
                                    "check it, or fill in the title, authors, journal and year by hand")
        CROSSREF_CACHE.parent.mkdir(exist_ok=True)
        CROSSREF_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True, ensure_ascii=False))
    return cache


def build_publications(entries, faculty):
    by_name = {}
    for f in faculty:
        by_name[f["name"].lower()] = f
        by_name[f["slug"]] = f
    for e in entries:
        e["doi"] = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", str(e.get("doi") or "").strip(), flags=re.I)
    looked_up = crossref_lookup([e["doi"] for e in entries if e["doi"]])

    pubs = []
    for e in entries:
        info = dict(looked_up.get(e["doi"], {}))
        info.update({k: v for k, v in e.items() if v not in (None, "", [])})  # typed-in values win
        if not info.get("title"):
            warnings.append(f"Publications: the entry with DOI '{e['doi']}' has no title and the DOI didn't work; skipped")
            continue
        info["link"] = info.get("link") or (f"https://doi.org/{e['doi']}" if e["doi"] else "")
        info["members"] = []
        for name in e.get("members") or []:
            person = by_name.get(str(name).lower())
            if person:
                info["members"].append(person)
                person["pub_count"] = person.get("pub_count", 0) + 1
            else:
                warnings.append(f"Publications: '{info['title'][:50]}…' lists unknown member '{name}'")
        info["year"] = int(info["year"]) if str(info.get("year") or "").isdigit() else None
        pubs.append(info)
    pubs.sort(key=lambda p: (-(p["year"] or 0), p["title"].lower()))
    return pubs


# ---------- assembling the site ----------

def load_everything():
    data = {}
    for name in ("fellows", "staff", "events", "publications"):
        value = load_yaml(ROOT / "data" / f"{name}.yml", [])
        if isinstance(value, dict):  # stored as "events: [...]" so the dashboard can collapse it
            value = value.get(name) or []
        data[name] = value

    areas = []
    for path in sorted((ROOT / "content/research").glob("*.md")):
        a = read_md(path)
        a["id"] = a["slug"]
        a["name"] = a.get("name") or a.get("title") or a["slug"].replace("-", " ").title()
        a["members"] = []
        areas.append(a)
    areas.sort(key=lambda a: a["name"].lower())
    area_lookup = {k: a for a in areas for k in (a["id"], a["name"].lower())}

    faculty = []
    for path in sorted((ROOT / "content/faculty").glob("*.md")):
        p = read_md(path)
        where = f"Faculty: {p.get('name') or path.name}"
        if not p.get("name"):
            warnings.append(f"{where}: no name; skipped")
            continue
        p["bio"] = p["content"]
        p["titles"] = p.get("titles") or []
        check_photo(p, where)
        for tag in p.get("areas") or []:
            area = area_lookup.get(str(tag).lower())
            if area:
                area["members"].append(p)
            else:
                warnings.append(f"{where}: unknown research area '{tag}'")
        faculty.append(p)
    faculty.sort(key=sort_key)
    for a in areas:
        a["members"].sort(key=sort_key)

    for group in ("fellows", "staff"):
        data[group] = [p for p in data[group] if isinstance(p, dict) and p.get("name")]
        for p in data[group]:
            check_photo(p, f"{ {'fellows': 'Fellows', 'staff': 'Administration'}[group]}: {p['name']}")
        data[group].sort(key=sort_key)

    today = dt.datetime.now(CHICAGO).date()  # GitHub's servers run on UTC
    events = []
    for e in data["events"]:
        e["date"] = to_date(e.get("date"), f"Events: '{e.get('title')}'")
        if e["date"] and e.get("title"):
            events.append(e)
    events.sort(key=lambda e: (e["date"], str(e.get("time") or "")))
    data["upcoming_events"] = [e for e in events if e["date"] >= today]
    data["past_events"] = [e for e in reversed(events) if e["date"] < today]

    news = []
    for path in sorted((ROOT / "content/news").glob("*.md")):
        n = read_md(path)
        if n.get("draft") or not n.get("title"):
            continue
        n["date"] = to_date(n.get("date") or path.stem[:10], f"News: '{n.get('title')}'")
        if not n["date"]:
            continue
        n["url"] = f"/news/{n['slug']}/"
        n["summary"] = n.get("summary") or plain_excerpt(n["content"])
        news.append(n)
    news.sort(key=lambda n: (n["date"], n["title"]), reverse=True)

    data.update(faculty=faculty, research_areas=areas, news=news,
                publications=build_publications(data["publications"], faculty))
    return data, today


def page_list(data):
    templates = {p.stem for p in (ROOT / "templates").glob("*.html")}
    pages = []
    for path in sorted((ROOT / "content").glob("*.md")):
        page = read_md(path)
        stem = path.stem
        page["layout"] = ("home" if stem == "index" else
                          stem if stem in templates and stem not in NOT_LAYOUTS and not stem.startswith("_")
                          else "page")
        page["url"] = {"index": "/", "404": "/404.html"}.get(stem, f"/{stem}/")
        pages.append(page)
    for area in data["research_areas"]:
        pages.append({"title": area["name"], "layout": "area", "area": area, "url": f"/research/{area['id']}/"})
    for post in data["news"]:
        pages.append({**post, "layout": "news_post"})
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="preview the site locally")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--base-path", default="",
                    help="URL prefix if the site is not at the domain root, e.g. /imb-website")
    ap.add_argument("--offline", action="store_true",
                    help="make a copy that opens straight from disk (double-click index.html), for demos")
    ap.add_argument("--out", type=Path, default=OUT, help="output folder (default: _site)")
    args = ap.parse_args()
    base = args.base_path.rstrip("/")
    out = args.out.resolve()
    if out == ROOT.resolve() or out in ROOT.resolve().parents or out == ROOT.resolve() / "static":
        sys.exit(f"ERROR: --out {out} would overwrite the project; choose an empty folder.")

    site = load_yaml(ROOT / "site.yml", {})
    menu = load_yaml(ROOT / "menu.yml", {})
    data, today = load_everything()
    for item in menu.get("nav", []):
        if item.get("children_from") == "research_areas":
            item["children"] = [{"title": a["name"], "url": f"/research/{a['id']}/"}
                                for a in data["research_areas"]] + (item.get("children") or [])
    site.update(menu)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT / "templates"),
                             autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["markdown"] = render_md
    env.filters["longdate"] = lambda d: f"{d:%A, %B} {d.day}, {d.year}"
    env.filters["shortdate"] = lambda d: f"{d:%B} {d.day}, {d.year}"

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "static", out)

    def offline_link(m, up):
        path, query, frag = re.match(r"([^?#]*)(\?[^#]*)?(#.*)?", m.group(2)).groups()
        if path == "" or path.endswith("/"):
            path += "index.html"
        return m.group(1) + up + path + (query or "") + (frag or "")

    def write(url, html_text):
        dest = out / url.lstrip("/")
        if not url.endswith(".html"):
            dest = dest / "index.html"
        if args.offline:  # turn "/about/" into e.g. "../about/index.html"
            up = "../" * (len(dest.relative_to(out).parts) - 1)
            html_text = re.sub(r"""(href="|src="|url=|url\(')/(?!/)([^"')\s]*)""",
                               lambda m: offline_link(m, up), html_text)
        elif base:  # prefix root-relative links when hosted in a sub-folder
            html_text = re.sub(r"""(href="|src="|url=|url\(')/(?!/)""", rf"\1{base}/", html_text)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html_text, encoding="utf-8")

    pages = page_list(data)
    for page in pages:
        tpl = env.get_template(f"{page['layout']}.html")
        write(page["url"], tpl.render(site=site, data=data, page=page, today=today))
    for old, new in load_yaml(ROOT / "redirects.yml", {}).items():
        write(old, env.get_template("redirect.html").render(target=new))

    # A private page at /site-status/ so editors can see problems without using GitHub.
    built_at = dt.datetime.now(CHICAGO).strftime("%B %-d, %Y at %-I:%M %p")
    write("/site-status/", env.get_template("status.html").render(
        site=site, data=data, today=today, warnings=warnings, built_at=built_at,
        page={"title": "Website status", "url": "/site-status/", "noindex": True}))

    for w in warnings:  # shown as yellow notes on GitHub; the site still publishes
        print(f"::warning::{w}" if os.environ.get("GITHUB_ACTIONS") else f"WARNING: {w}")
    print(f"Built {len(pages)} pages into {out}/")

    if args.serve:
        handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=out, **kw)
        print(f"Preview at http://localhost:{args.port}  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
