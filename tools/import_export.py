#!/usr/bin/env python3
"""Load every photo from an Instagram data export into the picker.

Instagram only shows the newest dozen posts to a logged out visitor, so the
whole back catalogue has to come from the export rather than the web:

    Instagram  >  Settings  >  Accounts Centre  >  Your information and
    permissions  >  Download your information  >  JSON, all time

Then point this at the zip (or the unzipped folder):

    python3 tools/import_export.py ~/Downloads/instagram-jgreerfilm.zip

It writes a thumbnail per photo into ig/thumbs/, rebuilds photos.manifest.js,
and leaves full size copies in ig/originals/ for whatever you pick. Carousels
are split, so each slide can be chosen on its own.
"""
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMBS = os.path.join(ROOT, "ig", "thumbs")
ORIGINALS = os.path.join(ROOT, "ig", "originals")
MANIFEST = os.path.join(ROOT, "photos.manifest.js")
THUMBPX = 440
FULLPX = 2000
IMG = (".jpg", ".jpeg", ".png", ".webp", ".heic")


def demojibake(s):
    """Instagram writes UTF-8 bytes through a latin-1 encoder. Undo that."""
    if not s:
        return ""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


class Source(object):
    """Reads uniformly from a zip or an unpacked folder."""

    def __init__(self, path):
        self.zip = zipfile.ZipFile(path) if zipfile.is_zipfile(path) else None
        self.root = None if self.zip else path
        self.names = (self.zip.namelist() if self.zip else
                      [os.path.relpath(os.path.join(dp, f), path)
                       for dp, _, fs in os.walk(path) for f in fs])

    def read(self, name):
        if self.zip:
            return self.zip.read(name)
        with open(os.path.join(self.root, name), "rb") as fh:
            return fh.read()

    def find_post_json(self):
        hits = [n for n in self.names
                if re.search(r"(posts_\d+|media)\.json$", n) and "/media/" in n.replace("\\", "/")]
        if not hits:
            hits = [n for n in self.names if re.search(r"posts_\d+\.json$", n)]
        return sorted(hits)

    def resolve(self, uri):
        """Export URIs are repo relative but prefixes vary between exports."""
        uri = uri.replace("\\", "/").lstrip("/")
        if uri in self.names:
            return uri
        tail = uri.split("/")[-1]
        for n in self.names:
            if n.replace("\\", "/").endswith("/" + tail) or n == tail:
                return n
        return None


def entries(doc):
    """Both shapes appear in the wild: a bare list, or {"ig_other_media": [...]}"""
    if isinstance(doc, dict):
        for k in ("ig_other_media", "ig_profile_picture", "photos", "media"):
            if isinstance(doc.get(k), list):
                return doc[k]
        return []
    return doc if isinstance(doc, list) else []


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = os.path.expanduser(sys.argv[1])
    if not os.path.exists(path):
        print("No such file or folder: %s" % path, file=sys.stderr)
        return 1

    src = Source(path)
    jsons = src.find_post_json()
    if not jsons:
        print("No posts_*.json inside that export. Make sure you asked Instagram "
              "for JSON rather than HTML.", file=sys.stderr)
        return 1
    print("Reading %s" % ", ".join(jsons))

    posts = []
    for name in jsons:
        try:
            posts.extend(entries(json.loads(src.read(name).decode("utf-8", "replace"))))
        except ValueError as e:
            print("  could not parse %s (%s)" % (name, e))

    os.makedirs(THUMBS, exist_ok=True)
    os.makedirs(ORIGINALS, exist_ok=True)

    manifest, keep_t, keep_o, skipped = [], set(), set(), 0
    for post in posts:
        media = post.get("media") or []
        post_cap = demojibake(post.get("title") or "")
        for idx, m in enumerate(media):
            uri = m.get("uri") or ""
            if not uri.lower().endswith(IMG):
                skipped += 1
                continue
            inner = src.resolve(uri)
            if not inner:
                skipped += 1
                continue
            ts = m.get("creation_timestamp") or post.get("creation_timestamp") or 0
            code = "x%s%s" % (ts, ("_%d" % idx) if len(media) > 1 else "")
            cap = demojibake(m.get("title") or "") or post_cap
            cap = cap.replace("\r", "").split("\n")[0][:70]

            tpath = os.path.join(THUMBS, code + ".jpg")
            opath = os.path.join(ORIGINALS, code + ".jpg")
            if not os.path.exists(tpath) or not os.path.exists(opath):
                try:
                    im = ImageOps.exif_transpose(Image.open(io.BytesIO(src.read(inner))))
                    im = im.convert("RGB")
                except Exception as e:
                    print("  skipped %s (%s)" % (uri, e))
                    skipped += 1
                    continue
                full = im.copy()
                full.thumbnail((FULLPX, FULLPX), Image.LANCZOS)
                full.save(opath, quality=86, optimize=True, progressive=True)
                th = im.copy()
                th.thumbnail((THUMBPX, THUMBPX), Image.LANCZOS)
                th.save(tpath, quality=78, optimize=True, progressive=True)

            keep_t.add(code + ".jpg")
            keep_o.add(code + ".jpg")
            manifest.append({
                "code": code,
                "caption": cap,
                "date": (datetime.fromtimestamp(ts, timezone.utc).strftime("%b %-d, %Y")
                         if ts else ""),
                "permalink": "",            # exports carry no shortcode
                "thumb": "ig/thumbs/%s.jpg" % code,
                "full": "ig/originals/%s.jpg" % code,
                "ts": ts,
            })

    if not manifest:
        print("Found no photos in that export.", file=sys.stderr)
        return 1

    manifest.sort(key=lambda p: p["ts"], reverse=True)

    for folder, keep in ((THUMBS, keep_t), (ORIGINALS, keep_o)):
        for stale in os.listdir(folder):
            if stale.endswith(".jpg") and stale not in keep:
                os.remove(os.path.join(folder, stale))

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("/* Written by tools/import_export.py from an Instagram data export.\n"
                 "   Every photo you have posted, newest first. Loaded by picker.html. */\n")
        fh.write("window.PHOTO_MANIFEST = " +
                 json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n")

    print("\n%d photos ready to pick from (%d non image items skipped)."
          % (len(manifest), skipped))
    print("Open picker.html, choose the ones you want, and save the result into "
          "photos.config.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
