#!/usr/bin/env python3
"""Add new food pictures to library/illustrations under the right file names.

Two ways in:

  1. PNGs exported by hand, each named after its Figma layer ("Seer fish.png", "Paneer.png"):
       python3 generator/tools/add_illustrations.py --dir ~/Downloads/new-pictures

  2. PNGs downloaded through the Figma connector, with a map of layer name -> image hash
     (see .claude/skills/add-illustrations/SKILL.md):
       python3 generator/tools/add_illustrations.py --dir <downloads> --map <map.json>

Names are matched against library/ingredients.csv (the name, the file name and every alias).
Add --dry-run to see what would happen, --replace to overwrite pictures that already exist.
"""
import csv, glob, hashlib, json, os, re, shutil, struct, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ILL = os.path.join(ROOT, "library", "illustrations")


def arg(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def key(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def index():
    idx = {}
    with open(os.path.join(ROOT, "library", "ingredients.csv")) as f:
        for r in csv.DictReader(f):
            for n in [r["name"], r["file"], *r["aliases"].split("|")]:
                if n.strip():
                    idx.setdefault(key(n), r["file"])
                    idx.setdefault(key(re.sub(r"\(.*?\)", "", n)), r["file"])
    return idx


def find(name, idx):
    for k in (key(name), key(re.sub(r"\(.*?\)", "", name))):
        if k in idx:
            return idx[k]
    return None


def png_info(path):
    b = open(path, "rb").read(64)
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h, depth, ctype = struct.unpack(">IIBB", b[16:26])
    return w, h, ctype in (4, 6) or b"tRNS" in open(path, "rb").read()


def main():
    d = arg("--dir")
    if not d or not os.path.isdir(d):
        sys.exit(__doc__)
    idx, dry, replace = index(), "--dry-run" in sys.argv, "--replace" in sys.argv
    pngs = sorted(glob.glob(os.path.join(d, "*.png")))
    if arg("--map"):   # [[layer name, imageHash], ...]: Figma's image hash is the SHA-1 of the file
        by_hash = {hashlib.sha1(open(p, "rb").read()).hexdigest(): p for p in pngs}
        pairs = [(name, by_hash.get(h)) for name, h in json.load(open(arg("--map")))]
    else:
        pairs = [(os.path.basename(p)[:-4], p) for p in pngs]

    added, exists, unknown, missing, problems = [], [], [], [], []
    for name, src in pairs:
        if not src:
            missing.append(name); continue
        f = find(name, idx)
        if not f:
            unknown.append(name); continue
        info = png_info(src)
        if not info:
            problems.append(f"{name}: not a PNG"); continue
        w, h, alpha = info
        if not alpha:
            problems.append(f"{name}: no transparent background (export it as PNG with the background turned off)"); continue
        if max(w, h) < 100:
            problems.append(f"{name}: only {w}×{h}px; export at 2x or 3x")
        dst = os.path.join(ILL, f + ".png")
        if os.path.exists(dst) and not replace:
            exists.append(f"{name} → {f}.png"); continue
        if not dry:
            shutil.copyfile(src, dst)
        added.append(f"{name} → {f}.png")

    say = "Would add" if dry else "Added"
    print(f"{say} {len(added)}:" if added else f"{say} nothing.")
    for x in added: print("  ", x)
    if exists:
        print(f"\nAlready in the library, left as they are ({len(exists)}; use --replace to swap them):")
        for x in exists: print("  ", x)
    if unknown:
        print(f"\nNot in the ingredient index ({len(unknown)}). Add a row for each in generator/tools/make_ingredients.py, then run this again:")
        for x in unknown: print("  ", x)
    if missing:
        print(f"\nIn the map but not downloaded ({len(missing)}):", ", ".join(missing))
    if problems:
        print("\nProblems:")
        for x in problems: print("  ", x)
    if added and not dry:
        subprocess.run([sys.executable, os.path.join(ROOT, "generator", "tools", "make_ingredients.py")])
    sys.exit(1 if unknown or missing or problems else 0)


main()
