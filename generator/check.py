# Read a household file, fill in the parts that are the same for every house, and check the rest.
# Used by build.py and make.py. Run on its own to check a file without building:
#   python3 generator/check.py profiles/<house>/household.json
import csv, json, os, re, sys, zlib

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GEN)
LIB = os.path.join(ROOT, "library")

# Text that is the same on every profile. A household file can still set its own.
DEFAULTS = {
    ("hero", "headline"): "Here’s a snapshot of your kitchen",
    ("hero", "about", "label"): "About your household",
    ("household", "title"): "Your household",
    ("meals", "title"): "Your meal preference",
    ("love", "title"): "Food you love",
    ("sources", "title"): "Where your food comes from",
    ("kitchen", "title"): "For your kitchen",
    ("noticed", "title"): "The little thing we noticed",
    ("rules", "title"): "Rules of the house",
    ("closing", "title"): "This is your kitchen as we know it",
    ("closing", "text"): "If we’ve missed anything or something changes, just let us know",
    ("closing", "cta"): "Drop us a voice note or a simple text and we’ll fix it",
}
DIETS = {"nonveg", "veg", "egg"}
SHELVES = ["chicken", "seafood", "eggs", "fresh", "mutton", "dairy", "bakery", "groceries"]
AVATARS = 24
# Names people use for an app -> the logo file's slug in library/logos/sources.csv
ALIAS = {"swiggy instamart": "instamart", "bb now": "bigbasket", "big basket": "bigbasket", "amazon fresh": "amazon", "amazon now": "amazon",
         "dmart": "dmart-ready", "nature's basket": "natures-basket", "fresh to home": "freshtohome", "prime cut": "primecut"}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", " ")).strip("-")


def logo_slug(name, known):
    k = name.lower().strip()
    k = slugify(ALIAS.get(k, k))
    return k if k in known else None


def join_names(names, last=" & "):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + last + names[-1]


def icons():
    return {f[:-4] for f in os.listdir(os.path.join(GEN, "fluent")) if f.endswith(".svg")}


def logo_slugs():
    with open(os.path.join(LIB, "logos", "sources.csv")) as f:
        return {r["slug"] for r in csv.DictReader(f)}


def pictures():
    return {f[:-4] for f in os.listdir(os.path.join(LIB, "illustrations")) if f.endswith(".png")}


def normalize(d):
    """Fill in everything that can be worked out, so a household file only holds what is true of that house."""
    people = d.setdefault("people", [])
    for p in people:
        if p.get("name"):
            p.setdefault("id", slugify(p["name"]))
        p.setdefault("noticed", [])
    names = [p["name"] for p in people if p.get("name")]
    if names:
        d.setdefault("title", join_names(names))
        d.setdefault("hero", {}).setdefault("greeting", "Hey " + join_names(names) + ",")
    if d.get("title"):
        d.setdefault("slug", slugify(d["title"]))
    # each person gets a different avatar; the same name always gets the same one
    used = {int(p["avatar"]) for p in people if str(p.get("avatar", "")).isdigit()}
    for p in people:
        if str(p.get("avatar", "")).isdigit() or not p.get("name"):
            continue
        n = zlib.crc32(p["name"].lower().encode()) % AVATARS + 1
        while n in used and len(used) < AVATARS:
            n = n % AVATARS + 1
        p["avatar"] = n
        used.add(n)
    for path, val in DEFAULTS.items():
        if path[0] == "kitchen" and "kitchen" not in d:
            continue
        node = d
        for k in path[:-1]:
            node = node.setdefault(k, {})
        node.setdefault(path[-1], val)
    d.setdefault("noticed", {}).setdefault("title", DEFAULTS[("noticed", "title")])
    return d


def validate(d):
    """Returns (errors, warnings). Errors stop the build; warnings are worth a look."""
    E, W = [], []
    ICONS, PICS = icons(), pictures()

    def need(cond, msg):
        if not cond:
            E.append(msg)
        return cond

    def icon(name, where):
        if name and name not in ICONS:
            W.append(f"{where}: there is no icon called “{name}”, so a plain food icon is shown. Icons are the file names in generator/fluent")

    def text_pairs(items, where):
        for i, x in enumerate(items or []):
            if not (isinstance(x, list) and 1 <= len(x) <= 2 and all(isinstance(s, str) and s.strip() for s in x)):
                E.append(f"{where} item {i + 1} must be [\"text\"] or [\"text\", \"smaller line under it\"]")

    if need(isinstance(d.get("slug"), str) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d.get("slug", "")), "slug must be lowercase words joined by hyphens, like “asha-bilal”"):
        pass
    H = d.get("hero", {})
    need(H.get("greeting"), "hero.greeting is missing")
    need(H.get("about", {}).get("big"), "hero.about.big is missing: one sentence about the household")
    if len(H.get("greeting", "")) > 36:
        W.append(f"hero.greeting is {len(H['greeting'])} characters; it gets small past 30. Try first names only")
    if len(H.get("about", {}).get("big", "")) > 150:
        W.append("hero.about.big is over 150 characters; keep it to one sentence")

    people = d.get("people", [])
    need(1 <= len(people) <= 4, f"people: the profile fits 1 to 4 people, this file has {len(people)}")
    ids, avs = set(), set()
    for i, p in enumerate(people):
        w = f"people[{i + 1}]"
        if not need(p.get("name"), f"{w} has no name"):
            continue
        w = p["name"]
        need(p.get("diet") in DIETS, f"{w}: diet must be nonveg, veg or egg")
        need(p["id"] not in ids, f"{w}: two people have the id “{p['id']}”; give one a different id")
        ids.add(p["id"])
        a = int(p.get("avatar", 0)) if str(p.get("avatar", "")).isdigit() else 0
        need(1 <= a <= AVATARS, f"{w}: avatar must be a number from 1 to {AVATARS}")
        if a in avs:
            W.append(f"{w}: avatar {a} is already used by someone else in this house")
        avs.add(a)
        for r in p.get("noticed", []):
            need(r.get("label") and r.get("value"), f"{w}: each “noticed” line needs a label and a value")
            icon(r.get("icon"), f"{w} noticed “{r.get('label')}”")

    cu = d.get("cuisines", [])
    need(1 <= len(cu) <= 6, f"cuisines: the profile shows 1 to 6, this file has {len(cu)}")
    for c in cu:
        need(c.get("name"), "a cuisine has no name")
        icon(c.get("icon"), f"cuisine {c.get('name')}")

    M = d.get("meals", {})
    need(M.get("items"), "meals.items is empty: add at least one meal")
    for m in M.get("items", []):
        need(m.get("name") and m.get("what"), "each meal needs a name and a “what”")
        for x in m.get("each", []):
            need(x.get("person") in ids, f"meal {m.get('name')}: “{x.get('person')}” is not one of the people's ids ({', '.join(sorted(ids))})")
        for a in m.get("art", []):
            need(a in PICS, f"meal {m.get('name')}: there is no picture called {a}.png in library/illustrations")
    for m in M.get("notes", []):
        need(m.get("label") and m.get("what"), "each meal note needs a label and a “what”")
        for a in m.get("art", []):
            need(a in PICS, f"meal note {m.get('label')}: there is no picture called {a}.png in library/illustrations")
    text_pairs(M.get("must"), "meals.must")
    text_pairs(M.get("nogo"), "meals.nogo")

    L = d.get("love", {})
    for k in ("often", "later"):
        for x in L.get(k, []):
            if len(x) > 30:
                W.append(f"love.{k}: “{x}” is long for a chip; keep dish names under 30 characters")

    if "spice" in d:
        need(d["spice"].get("level") in (1, 2, 3), "spice.level must be 1 (mild), 2 (medium) or 3 (hot). Leave spice out if the notes don't say")
    for p in d.get("proteins", []):
        need(p.get("name"), "each protein needs a name")
        if "freq" in p:
            need(p["freq"] in (1, 2, 3, 4) and p.get("label"), f"protein {p.get('name')}: freq must be 1 to 4 (dots shown) and needs a label. Leave both out if the notes don't say how often")

    S = d.get("sources", {})
    need(S.get("groups"), "sources.groups is empty: add at least one shelf")
    for g in S.get("groups", []):
        k = g.get("kind", "")
        if k not in SHELVES and not g.get("title"):
            W.append(f"shelf “{k}” is not one of {', '.join(SHELVES)}; give it a title")
        if k not in SHELVES and not g.get("items"):
            W.append(f"shelf “{k}” has no items, so it has no pictures")
    diets = {p.get("diet") for p in people}
    if diets == {"veg"}:
        bad = [g["kind"] for g in S.get("groups", []) if g.get("kind") in ("chicken", "seafood", "mutton", "eggs")]
        if bad:
            W.append(f"everyone is vegetarian but the shelves include {', '.join(bad)}")
    K = d.get("kitchen")
    if K:
        text_pairs(K.get("must"), "kitchen.must")
        text_pairs(K.get("nogo"), "kitchen.nogo")

    R = d.get("rules", {})
    for f in R.get("facts", []):
        need(f.get("topic") and f.get("value") and f.get("sub"), "each rule tile needs a topic, a value and a sub")
        icon(f.get("icon"), f"rule “{f.get('topic')}”")
        if len(f.get("value", "")) > 10:
            W.append(f"rule “{f.get('topic')}”: the big value “{f.get('value')}” is over 10 characters; it is meant to be short, like “3 days”")
    text_pairs(R.get("must"), "rules.must")
    text_pairs(R.get("nogo"), "rules.nogo")

    for k in ("household", "meals", "love", "sources", "noticed", "rules") + (("kitchen",) if "kitchen" in d else ()):
        if not d.get(k, {}).get("sub"):
            W.append(f"{k}.sub is empty, so the section has a title and no line under it")

    # house writing rules: plain and calm, about the household and not about who orders
    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)
    for s in strings(d):
        if "!" in s:
            W.append(f"“{s}” has an exclamation mark; the profile's voice is calm")
        if re.search(r"\b(who orders|orders the|places the order|decides the menu|decides what)\b", s, re.I):
            W.append(f"“{s}” is about who orders or decides; leave that out of the profile")
    return E, W


def load(path):
    with open(path) as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError as x:
            sys.exit(f"{path} is not valid JSON: line {x.lineno}, column {x.colno}: {x.msg}")
    d = normalize(d)
    E, W = validate(d)
    for w in W:
        print("warning:", w)
    if E:
        print("\nThe household file needs fixing before it can be built:")
        for x in E:
            print(" -", x)
        sys.exit(1)
    return d


if __name__ == "__main__":
    d = load(sys.argv[1])
    print(f"OK: {d['title']} ({d['slug']}), {len(d['people'])} people, avatars {[p['avatar'] for p in d['people']]}")
