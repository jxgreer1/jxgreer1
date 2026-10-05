#!/usr/bin/env python3
"""Apply photos.config.json to the site.

Reads photos.manifest.js (whatever filled it: the Instagram export importer or
a feed sync), picks according to photos.config.json, copies the chosen photos
into ig/ and rewrites the POSTS array in index.html.

    python3 tools/build_gallery.py
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "photos.manifest.js")
CONFIG = os.path.join(ROOT, "photos.config.json")
PAGE = os.path.join(ROOT, "index.html")
IGDIR = os.path.join(ROOT, "ig")

try:
    from PIL import Image
except ImportError:
    Image = None


def read_manifest():
    with open(MANIFEST, encoding="utf-8") as fh:
        s = fh.read()
    return json.loads(s[s.index("["):s.rindex("]") + 1])


def read_config():
    cfg = {"mode": "auto", "limit": 12, "hide": [], "order": []}
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as fh:
            cfg.update({k: v for k, v in json.load(fh).items() if not k.startswith("_")})
    return cfg


def choose(items, cfg):
    by = {p["code"]: p for p in items}
    if cfg.get("mode") == "manual":
        picked = [by[c] for c in cfg.get("order") or [] if c in by]
        if picked:
            return picked
        print("  manual mode matched nothing; using auto.")
    pool = items
    if cfg.get("onePerPost", True):
        # a six slide carousel would otherwise eat the whole page
        pool = [p for p in items
                if "_" not in p["code"] or p["code"].endswith("_1")]
        if len(pool) != len(items):
            print("  one slide per post: %d of %d" % (len(pool), len(items)))
    hide = set(cfg.get("hide") or [])
    return [p for p in pool if p["code"] not in hide][:int(cfg.get("limit") or 12)]


def js(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    if not os.path.exists(MANIFEST):
        print("No photos.manifest.js yet. Run tools/import_export.py first.",
              file=sys.stderr)
        return 1
    items = read_manifest()
    cfg = read_config()
    picked = choose(items, cfg)
    if not picked:
        print("Config selected nothing; leaving the site alone.")
        return 0

    rows, keep = [], set()
    for n, p in enumerate(picked, start=1):
        src = os.path.join(ROOT, p.get("full") or p.get("thumb"))
        if not os.path.exists(src):
            print("  missing file for %s, skipped" % p["code"])
            continue
        name = "%02d.jpg" % n
        dst = os.path.join(IGDIR, name)
        shutil.copyfile(src, dst)
        keep.add(name)
        if Image:
            with Image.open(dst) as im:
                w, h = im.size
        else:
            w = h = 0
        rows.append('    {f:%s, w:%d,h:%d, t:%s, d:%s, p:%s, u:%s}' % (
            js(name), w, h, js(p.get("caption") or "Untitled"),
            js(p.get("date") or ""), js(p["code"]), js(p.get("permalink") or "")))
        print("  %s  %dx%d  %s" % (name, w, h, (p.get("caption") or "")[:40]))

    if not rows:
        print("Nothing to publish.")
        return 0

    for stale in os.listdir(IGDIR):
        if stale.endswith(".jpg") and stale not in keep:
            os.remove(os.path.join(IGDIR, stale))
            print("  removed stale %s" % stale)

    page = open(PAGE, encoding="utf-8").read()
    block = ("  /* POSTS:START -- rewritten by the tools in tools/, do not hand edit */\n"
             "  var POSTS = [\n" + ",\n".join(rows) + "\n  ];\n"
             "  /* POSTS:END */")
    new, count = re.subn(r"  /\* POSTS:START.*?/\* POSTS:END \*/", block, page,
                         count=1, flags=re.S)
    if not count:
        print("ERROR: POSTS markers not found in index.html", file=sys.stderr)
        return 1
    open(PAGE, "w", encoding="utf-8").write(new)
    print("\nindex.html now shows %d of %d photos." % (len(rows), len(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
