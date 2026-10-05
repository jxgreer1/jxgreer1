#!/usr/bin/env python3
"""Pull the latest @jgreerfilm posts into this repo.

Reads a Behold.so JSON feed (env BEHOLD_FEED_URL), downloads each still,
writes it into ig/, and rewrites the POSTS array inside index.html between
the POSTS:START and POSTS:END markers. Designed to be run by CI on a
schedule; safe to run by hand too.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

from PIL import Image, ImageOps

FEED = os.environ.get("BEHOLD_FEED_URL", "").strip()
LIMIT = int(os.environ.get("POST_LIMIT", "12"))
MAXPX = 2000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGDIR = os.path.join(ROOT, "ig")
PAGE = os.path.join(ROOT, "index.html")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
    return raw if binary else raw.decode("utf-8", "replace")


def normalise(doc):
    """Behold returns {posts:[...]}; some feeds return a bare list."""
    items = doc if isinstance(doc, list) else (
        doc.get("posts") or doc.get("media") or doc.get("data") or [])
    out = []
    for m in items:
        if str(m.get("mediaType", "")).upper() == "VIDEO":
            continue
        sizes = m.get("sizes") or {}
        best = sizes.get("full") or sizes.get("large") or sizes.get("medium") or {}
        url = best.get("mediaUrl") or m.get("mediaUrl") or m.get("media_url")
        if not url:
            continue
        link = m.get("permalink", "")
        code = re.search(r"/p/([^/?]+)", link)
        caption = (m.get("caption") or "").strip().replace("\r", "")
        out.append({
            "url": url,
            "permalink": link,
            "code": code.group(1) if code else "",
            "caption": caption.split("\n")[0][:70],
            "ts": m.get("timestamp") or "",
        })
        if len(out) >= LIMIT:
            break
    return out


def pretty_date(ts):
    if not ts:
        return ""
    try:
        d = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return "%s %d, %d" % (d.strftime("%b"), d.day, d.year)


def js(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    if not FEED:
        print("BEHOLD_FEED_URL is not set. Nothing to do.")
        print("Create a free feed at behold.so, then add the URL as a repo "
              "variable named BEHOLD_FEED_URL.")
        return 0

    posts = normalise(json.loads(fetch(FEED)))
    if not posts:
        print("Feed returned no still images; leaving the site untouched.")
        return 0

    os.makedirs(IGDIR, exist_ok=True)
    rows, keep = [], set()
    for n, p in enumerate(posts, start=1):
        name = "%02d.jpg" % n
        path = os.path.join(IGDIR, name)
        try:
            raw = fetch(p["url"], binary=True)
        except Exception as e:                      # one bad URL must not kill the run
            print("  skip %s (%s)" % (name, e))
            continue
        with open(path, "wb") as fh:
            fh.write(raw)
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im.thumbnail((MAXPX, MAXPX), Image.LANCZOS)
        im.save(path, quality=85, optimize=True, progressive=True)
        keep.add(name)
        rows.append('    {f:%s, w:%d,h:%d, t:%s, d:%s, p:%s}' % (
            js(name), im.width, im.height,
            js(p["caption"] or "Untitled"), js(pretty_date(p["ts"])), js(p["code"])))
        print("  %s  %dx%d  %s" % (name, im.width, im.height, p["caption"][:40]))

    if not rows:
        print("Nothing downloaded; leaving the site untouched.")
        return 0

    for stale in os.listdir(IGDIR):
        if stale.endswith(".jpg") and stale not in keep:
            os.remove(os.path.join(IGDIR, stale))
            print("  removed stale %s" % stale)

    page = open(PAGE, encoding="utf-8").read()
    block = ("  /* POSTS:START -- rewritten by tools/sync_instagram.py, do not hand edit */\n"
             "  var POSTS = [\n" + ",\n".join(rows) + "\n  ];\n"
             "  /* POSTS:END */")
    new, count = re.subn(
        r"  /\* POSTS:START.*?/\* POSTS:END \*/", block, page,
        count=1, flags=re.S)
    if not count:
        print("ERROR: POSTS markers not found in index.html", file=sys.stderr)
        return 1
    if new != page:
        open(PAGE, "w", encoding="utf-8").write(new)
        print("index.html updated with %d posts." % len(rows))
    else:
        print("Already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
