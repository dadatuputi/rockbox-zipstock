"""Tag each audiobook with its series and number, so Rockbox can list books
by author, then series, then 1 to N, with short names.

Rockbox's database knows only what is in the files' tags. This reads the
series from the plugin's index (<card>/.absh/index.json), which holds what
Audiobookshelf says, and writes into each .m4b:

    grouping   the series, e.g. "Harry Potter"     (books with none: "Standalone books")
    disc       the number in the series, e.g. 5
    album      a short title: the words every book in the series starts with
               are dropped, so "Harry Potter and the Order of the Phoenix"
               becomes "Order of the Phoenix". A closing tag such as
               "(Full Cast)" in the folder name goes first, so two editions
               differ in the part of the line the screen shows:
               "(Full Cast) Order of the Phoenix".

The tags are changed in place with mutagen; the audio is not touched. The old
values go to <card>/.absh/tag-books-undo.json, and --undo puts them back.

Needs mutagen (pip3 install mutagen). Shows what it would do, and writes
nothing, unless you add --apply:

    python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS
    python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS --apply
    python3 tag-books.py /Volumes/MUSICSD/AUDIOBOOKS --undo

Then rebuild the database on the player: Settings > General Settings >
Database > Initialize Now, and restart it.
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    from mutagen.mp4 import MP4
except ImportError:
    sys.exit("Needs mutagen: pip3 install mutagen")

STANDALONE = "Standalone books"
SERIES = re.compile(r"^(.*?)\s*#\s*([\d.]+)\s*$")
TAG = re.compile(r"\s*\(([^()]{1,30})\)\s*$")


def pick_series(raw, title):
    """ABS joins several series with ", ": "Wizarding World #5, Harry Potter #5".
    Prefer the one whose name is in the title, else the first."""
    found = []
    for part in re.split(r",\s*(?=[^,]*#)", raw or ""):
        m = SERIES.match(part.strip())
        if m:
            found.append((m.group(1).strip(), m.group(2)))
        elif part.strip():
            found.append((part.strip(), ""))
    if not found:
        return "", ""
    for name, num in found:
        if name.lower() in (title or "").lower():
            return name, num
    return found[0]


def common_words(titles):
    """How many leading words every title shares, always leaving at least one:
    4 for "Harry Potter and the ..." titles."""
    words = [t.split() for t in titles]
    n = 0
    while all(len(w) > n + 1 for w in words) and len({w[n].lower() for w in words}) == 1:
        n += 1
    return n


def short_titles(books):
    """Book key -> short title, per series."""
    by_series = {}
    for key, b in books.items():
        by_series.setdefault(b["series"], []).append(key)
    out = {}
    for series, keys in by_series.items():
        titles = [books[k]["title"] for k in keys]
        n = common_words(titles) if series and len(keys) > 1 else 0
        for k in keys:
            t = books[k]["title"]
            if n:
                t = " ".join(t.split()[n:])
            elif series and t.lower().startswith(series.lower()):
                rest = t[len(series):].lstrip(" :,-")
                t = rest or t
            # editions: put the folder's closing tag first, e.g. "(Full Cast)",
            # so it shows before the 96px row cuts the line off
            tag = TAG.search(books[k]["folder"])
            if tag and tag.group(1).lower() not in t.lower() and "#" not in tag.group(1):
                t = f"({tag.group(1)}) {t}"
            out[k] = t[0].upper() + t[1:] if t else books[k]["title"]
    return out


def load_books(root):
    index_path = root.parent / ".absh" / "index.json"
    try:
        entries = json.loads(index_path.read_text(encoding="utf-8")).get("entries", {})
    except (OSError, ValueError):
        entries = {}
        print(f"No plugin index at {index_path}; using the tags already in the files.")
    books = {}
    for folder in sorted(p for p in root.iterdir() if not p.name.startswith(".")):
        files = sorted(folder.glob("*.m4b")) if folder.is_dir() else (
            [folder] if folder.suffix.lower() == ".m4b" else [])
        files = [f for f in files if not f.name.startswith("._")]
        if not files:
            continue
        rec = entries.get(folder.name) or {}
        title, series_raw = rec.get("title") or "", rec.get("series") or ""
        if not title:
            tags = MP4(files[0]).tags or {}
            title = (tags.get("\xa9alb") or tags.get("\xa9nam") or [folder.stem])[0]
        series, num = pick_series(series_raw, title)
        books[folder.name] = {"folder": folder.name, "files": files, "title": title,
                              "series": series, "num": num}
    return books


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1]).expanduser()
    apply, undo = "--apply" in sys.argv, "--undo" in sys.argv
    undo_path = root.parent / ".absh" / "tag-books-undo.json"

    if undo:
        saved = json.loads(undo_path.read_text(encoding="utf-8"))
        for path, old in saved.items():
            f = MP4(path)
            for k, v in old.items():
                if v is None:
                    f.tags.pop(k, None)
                else:
                    f.tags[k] = [tuple(x) for x in v] if k == "disk" else v
            f.save()
            print("restored", path)
        return

    books = load_books(root)
    short = short_titles(books)
    saved = json.loads(undo_path.read_text(encoding="utf-8")) if undo_path.exists() else {}
    changes = 0
    print(f"{'series':24} {'#':>4}  short title")
    for key, b in sorted(books.items(), key=lambda kv: (kv[1]["series"] or "~", float(kv[1]["num"] or 0))):
        series = b["series"] or STANDALONE
        print(f"{series[:24]:24} {b['num'] or '':>4}  {short[key]}")
        for f in b["files"]:
            mp4 = MP4(f)
            if mp4.tags is None:
                mp4.add_tags()
            t = mp4.tags
            want = {"\xa9grp": [series], "\xa9alb": [short[key]]}
            if b["num"]:
                want["disk"] = [(int(float(b["num"])), 0)]
            if all(t.get(k) == v for k, v in want.items()):
                continue
            changes += 1
            if apply:
                saved.setdefault(str(f.resolve()), {k: (list(map(list, t[k])) if k == "disk" else t[k])
                                          if k in t else None for k in want})
                t.update(want)
                mp4.save()
    if apply:
        undo_path.parent.mkdir(parents=True, exist_ok=True)
        undo_path.write_text(json.dumps(saved, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nTagged {changes} files. Old tags are in {undo_path}.")
    else:
        print(f"\n{changes} files would change. Add --apply to write the tags.")


if __name__ == "__main__":
    main()
