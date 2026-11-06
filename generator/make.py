#!/usr/bin/env python3
"""Make a household profile in one step: check the household file, build the page, check that every
line fits, then make the PDF.

usage:
  python3 generator/make.py profiles/<house>/household.json
  python3 generator/make.py <house>                 (same thing, using the folder name)
  python3 generator/make.py <house> --no-pdf        (page only, faster while editing)
  python3 generator/make.py <house> --contrast      (also list text that fails the contrast check)
"""
import json, os, re, subprocess, sys

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GEN)
TOOLS = os.path.join(GEN, "tools")
CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
# lines that fail contrast on purpose or are waiting on a design decision (see CLAUDE.md)
KNOWN_CONTRAST = ("[k] About your household", "[tag] Household Profile", "[chip o]", "[SPAN]")


def find_file(arg):
    for p in (arg, os.path.join(arg, "household.json"), os.path.join(ROOT, "profiles", arg, "household.json")):
        if os.path.isfile(p):
            return os.path.abspath(p)
    sys.exit(f"Can't find a household file for “{arg}”. Expected profiles/{arg}/household.json")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    src = find_file(args[0])
    chrome = os.environ.get("CHROME") or next((c for c in CHROMES if os.path.exists(c)), None)
    if not chrome:
        sys.exit("Google Chrome is needed to check the page and make the PDF. Install it from google.com/chrome, then run this again.")
    env = dict(os.environ, CHROME=chrome)

    # 1 build (build.py checks the file first and stops with a list of what to fix)
    b = run([sys.executable, os.path.join(GEN, "build.py"), src], env=env)
    warnings = [l[len("warning: "):] for l in b.stdout.splitlines() if l.startswith("warning: ")]
    if b.returncode != 0:
        print(b.stdout.replace("warning: ", "Worth a look: "), b.stderr, sep="")
        sys.exit(1)
    html = next(l for l in b.stdout.splitlines() if l.endswith(".html"))
    out = os.path.dirname(html)
    report = json.load(open(os.path.join(out, "report.json")))

    # 2 render it at phone width: page height, text that runs past its card, contrast
    m = run([sys.executable, os.path.join(TOOLS, "measure.py"), html, "390"], env=env)
    hm = re.search(r"page height (\d+)px", m.stdout)
    if not hm:
        print(m.stdout, m.stderr)
        sys.exit("Chrome couldn't render the page. Is Chrome up to date and allowed to run?")
    height = int(hm.group(1))
    over = [l[len("OVERFLOW"):].strip() for l in m.stdout.splitlines() if l.startswith("OVERFLOW")]
    contrast = [l.strip() for l in m.stdout.splitlines() if "FAIL" in l and not any(k in l for k in KNOWN_CONTRAST)]

    # 3 PDF
    pdf = os.path.join(out, os.path.basename(html)[:-5] + ".pdf")
    if "--no-pdf" not in sys.argv:
        title = re.search(r"<title>(.*?)</title>", open(html).read()).group(1)
        p = run(["/bin/zsh", os.path.join(TOOLS, "pdf.sh"), html, str(height), pdf], env=dict(env, PDF_TITLE=__import__("html").unescape(title)))
        if p.returncode != 0 or not os.path.exists(pdf):
            print(p.stdout, p.stderr)
            sys.exit("The PDF step failed. It needs the Xcode command line tools: run  xcode-select --install")
        shot = os.path.join(TOOLS, ".tmp", "_shot.png")
        if os.path.exists(shot):
            os.replace(shot, os.path.join(out, "preview-full-page.png"))

    # 4 what to tell the person
    rel = lambda p: os.path.relpath(p, ROOT)
    print(f"Page: {rel(html)}")
    if "--no-pdf" not in sys.argv:
        print(f"PDF:  {rel(pdf)}  ({height}px tall)")
    problems = 0
    if over:
        problems += len(over)
        print("\nText that doesn't fit (shorten it in the household file):")
        for o in over:
            print("  -", re.sub(r"^\d+\s+(\+0px past \[shelf\] )?", "", o))
    if report.get("missing_art"):
        print("\nNo picture yet (a plain icon is shown; ask the designer to draw it):")
        for x in report["missing_art"]:
            print("  -", x)
    generic = [x.split(":")[0] for x in report.get("auto_art", []) if x.endswith(": none")]
    if generic:
        print("\nNo food word found, so these show a generic picture (set their `art`):")
        for x in generic:
            print("  -", x)
    tiles = sorted(set(report.get("text_logos", [])))
    if tiles:
        print("\nShown as a text tile, because there's no logo for them (that's fine):")
        for x in tiles:
            print("  -", x)
    if report.get("stand_ins"):
        print("\nUsing a similar picture for now:")
        for x in report["stand_ins"]:
            print("  -", x)
    if report.get("unknown_people"):
        problems += 1
        print("\nMeal rows for people who aren't in the house (they were left out):", ", ".join(report["unknown_people"]))
    if warnings:
        print("\nWorth a look:")
        for w in warnings:
            print("  -", w)
    if contrast and "--contrast" in sys.argv:
        print("\nHard to read (contrast):")
        for c in contrast:
            print("  -", c)
    print("\nReady to send." if not problems else "\nFix the items above and run this again before sending.")
    sys.exit(2 if problems else 0)


main()
