#!/usr/bin/env python3
"""Check every link and image in the built site.

    python build.py && python tools/check_links.py            # internal + external
    python tools/check_links.py --internal-only               # skip web requests

Internal links must point to a file in _site/. External links are fetched; some
publishers (journals, doi.org) answer automated requests with 403 even though
the link works in a browser, so treat 403s as "check by hand".
"""
import argparse
import concurrent.futures
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", default=ROOT / "_site", type=pathlib.Path)
    ap.add_argument("--internal-only", action="store_true")
    args = ap.parse_args()

    broken, external = [], set()
    for page in args.site.rglob("*.html"):
        for url in re.findall(r'(?:href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
            if url.startswith(("http://", "https://")):
                external.add(url)
            elif not url.startswith(("mailto:", "tel:", "#")):
                target = args.site / re.split(r"[#?]", url)[0].lstrip("/")
                if not (target.is_file() or (target / "index.html").is_file()):
                    broken.append(f"{page.relative_to(args.site)} -> {url}")
    print("Internal links broken:", len(broken))
    for b in broken:
        print("  ", b)

    if args.internal_only:
        return
    def check(url):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            return url, urllib.request.urlopen(req, timeout=20).status
        except Exception as e:
            return url, getattr(e, "code", type(e).__name__)
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        bad = [(u, s) for u, s in pool.map(check, sorted(external)) if s != 200]
    print(f"External links checked: {len(external)}, not OK: {len(bad)}")
    for u, s in sorted(bad, key=lambda x: str(x[1])):
        print(f"   {s}  {u}")


if __name__ == "__main__":
    main()
