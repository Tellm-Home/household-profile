# Household profile v7 — one template, any household.
# usage: python3 generator/build.py profiles/<house>/household.json [out_dir]
# (Most people should run make.py instead: it builds, checks the fit and makes the PDF.)
# Reads the household JSON, picks illustrations, avatars, logos and Fluent icons from /library,
# copies only what the page uses into <out>/assets, and writes <out>/household-<slug>.html.
# Design source: Figma oNxq6P6BXhjgCKiZENgWb3, frame 199:463 (the final flow).
import csv, html, json, math, os, re, shutil, struct, sys
import check

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GEN)
LIB = os.path.join(ROOT, "library")
FL = os.path.join(GEN, "fluent")
PILL = open(os.path.join(GEN, "m-pill.txt")).read()

SRC = os.path.abspath(sys.argv[1])
data = check.load(SRC)   # fills in the standard text and avatars, stops on mistakes
SLUG = data["slug"]
# a household.json inside its own folder builds into that folder; anything else into profiles/<slug>
OUT = sys.argv[2] if len(sys.argv) > 2 else (os.path.dirname(SRC) if os.path.basename(SRC) == "household.json" else os.path.join(ROOT, "profiles", SLUG))
REPORT = {"missing_art": [], "stand_ins": [], "text_logos": [], "auto_art": []}
COPY = {}  # dest rel path -> source abs path

def e(s): return html.escape(str(s), quote=False)
def ea(s): return html.escape(str(s), quote=True)
def asset(kind, src, name=None):
    rel = f"assets/{kind}/{name or os.path.basename(src)}"
    COPY[rel] = src
    return rel

# ---------- Fluent icons (Fluent UI System Icons, MIT) ----------
_FL = {}
def fi(name, s=18, cls="i"):
    if name not in _FL:
        p = os.path.join(FL, f"{name}.svg")
        if not os.path.exists(p): p = os.path.join(FL, "food.svg")
        svg = open(p).read()
        _FL[name] = (re.search(r'viewBox="([^"]+)"', svg).group(1), re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1))
    vb, inner = _FL[name]
    return f'<svg class="{cls}" width="{s}" height="{s}" viewBox="{vb}" fill="currentColor" aria-hidden="true">{inner}</svg>'
CHECK = lambda: fi("checkmark_12f", 12, "")
CROSS = lambda: fi("dismiss_12f", 10, "")

def M(w=72, col="#A96ADD"):
    return f'<svg viewBox="140 140 317.2 138.1" width="{w}" height="{round(w*138.1/317.2)}" role="img" aria-label="M"><path d="{PILL}" fill="{col}"/></svg>'

# ---------- illustrations: words in the data -> library pictures ----------
ILL = os.path.join(LIB, "illustrations")
# The index (library/ingredients.csv, made by tools/make_ingredients.py) maps every name a household might
# use to a picture file. A file that is not drawn yet falls back to its stand-in, or to a placeholder.
HAVE = {f[:-4] for f in os.listdir(ILL) if f.endswith(".png")}
INDEX = []   # (alias, file, stand_in, name)
with open(os.path.join(LIB, "ingredients.csv")) as f:
    for r in csv.DictReader(f):
        for a in r["aliases"].split("|") + [r["name"].lower()]:
            if a.strip(): INDEX.append((a.strip().lower(), r["file"], r["stand_in"], r["name"]))
# dishes are not ingredients: they borrow the picture of what they are made from
DISH = [("salad", ["tomato-fresh", "spinach"]), ("sabzi", ["spinach"]), ("vegetables", ["tomato-fresh", "spinach"]), ("veggies", ["tomato-fresh", "spinach"]),
        ("roti", ["flour"]), ("chapati", ["flour"]), ("phulka", ["flour"]), ("paratha", ["flour"]), ("upma", ["semolina"]),
        ("biryani", ["rice"]), ("pulao", ["rice"]), ("khichdi", ["rice"]), ("fried rice", ["rice"]), ("fruit", ["banana"]), ("juice", ["orange"])]
PATS = sorted([(a, [f], s, nm) for a, f, s, nm in INDEX] + [(d, fs, "", d) for d, fs in DISH], key=lambda x: -len(x[0]))
def resolve(file, stand, name):
    if file in HAVE: return file
    if stand and stand in HAVE:
        REPORT["stand_ins"].append(f"{name} → {stand} (draw {file}.png)"); return stand
    REPORT["missing_art"].append(f"{name} (draw {file}.png)"); return None
def art_for(text, n=2):
    """Pictures for the ingredients a phrase mentions, in the order they appear."""
    t = " " + text.lower() + " "; taken = []; hits = []
    for a, files, stand, name in PATS:   # longest names first, so "chicken breast" beats "chicken"
        for m in re.finditer(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", t):
            if any(m.start() < e2 and s2 < m.end() for s2, e2 in taken): continue
            taken.append((m.start(), m.end())); hits.append((m.start(), files, stand, name))
    out = []
    for _, files, stand, name in sorted(hits, key=lambda h: h[0]):
        if len(out) >= n: break
        for f in files:
            r = resolve(f, stand, name)
            if r and r not in out: out.append(r)
    return out[:n]
def ill(slug, cls="", style=""):
    p = os.path.join(ILL, f"{slug}.png")
    return f'<img{f" class={cls}" if cls else ""} src="{asset("illustrations", p)}" alt=""{f" style={chr(34)}{style}{chr(34)}" if style else ""}>'

# ---------- avatars ----------
def ava(person, s=40, cls="ava"):
    n = int(person["avatar"])
    p = os.path.join(LIB, "avatars", f"avatar-{n:02d}.png")
    return f'<img class="{cls}" src="{asset("avatars", p)}" alt="{ea(person["name"])}" width="{s}" height="{s}">'
PEOPLE = {p["id"]: p for p in data["people"]}

# ---------- logos: library first, text tile when a vendor has none ----------
LOGOS = {}
with open(os.path.join(LIB, "logos", "sources.csv")) as f:
    for r in csv.DictReader(f):
        b = open(os.path.join(LIB, "logos", r["file"]), "rb").read(24)
        w, h = struct.unpack(">II", b[16:24])
        LOGOS[r["slug"]] = {"name": r["name"].split(" (")[0], "kind": r["kind"], "file": r["file"], "w": w, "h": h}
def logo_key(x): return check.logo_slug(x, LOGOS)   # loose names: "Swiggy Instamart" -> instamart
def text_size(name, box=57):
    longest = max(len(w) for w in name.split())
    for s in (11, 10, 9):
        if longest * 0.6 * s <= box: return s
    return 9
def logo(x, size="tile"):
    """size tile = 65x41 household tile; size app = 84x52 source tile."""
    k = logo_key(x)
    if not k:
        REPORT["text_logos"].append(x)
        fs = text_size(x, 57 if size == "tile" else 72) + (0 if size == "tile" else 2)
        return f'<span class="tx" style="font-size:{fs}px;line-height:{fs+1}px">{e(x)}</span>'
    L = LOGOS[k]; src = asset("logos", os.path.join(LIB, "logos", L["file"]))
    if L["kind"] == "app icon":
        return f'<img class="sq" src="{src}" alt="{ea(L["name"])}">'
    wide = L["w"] / L["h"] >= 1.5
    return f'<img class="{"mk" if wide else "mq"}" src="{src}" alt="{ea(L["name"])}">'

# ---------- shared pieces ----------
DIET = {"nonveg": ("Non-veg", "nv"), "veg": ("Vegetarian", "vg"), "egg": ("Eggetarian", "eg")}
def diet(k):
    label, c = DIET.get(k, DIET["nonveg"])
    return f'<span class="diet {c}"><span class="mark"><i></i></span>{label}</span>'
def bg(name, wash=None):
    src = asset("bg", os.path.join(LIB, "backgrounds", f"{name}.jpg"))
    w = f";--wash:{wash}" if wash else ""
    return f'<div class="bgl" style="--img:url({src}){w}" aria-hidden="true"></div>'
def head(t, s, sid):
    return f'<div class="head rv"><h2 id="{sid}">{e(t)}</h2>{f"<p class=sum>{e(s)}</p>" if s else ""}</div>'
def rc(k, items, extra=""):
    y = k == "y"; sym = CHECK() if y else CROSS()
    rows = "".join(f'<li><span class="mk">{sym}</span><span class="t">{e(x[0])}{f"<span class=s13>{e(x[1])}</span>" if len(x) > 1 else ""}</span></li>' for x in items)
    return f'<div class="rc {k}"><div class="hd"><span class="bdg">{sym}</span><b>{"Must-haves" if y else "No-gos"}</b></div><ul>{rows}</ul>{extra}</div>'
def pair(must, nogo, extra="", nt=None):
    st = f' style="--nt:{nt}"' if nt else ""
    return f'<div class="rcs rv"{st}>' + (rc("y", must) if must else "") + (rc("n", nogo, extra) if nogo else "") + "</div>"
def dots(n): return '<span class="dots" aria-hidden="true">' + "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(4)) + "</span>"
CHIP_ICON = [(r"\begg", "food_egg"), (r"carrot", "food_carrot"), (r"chicken|mutton|meat|keema|lamb|pork|beef", "food_chicken_leg"),
             (r"fish|prawn|seer|mackerel|sardine|crab|pomfret|shrimp", "food_fish"), (r"salad|greens|sabzi|veg", "bowl_salad"),
             (r"rice|poha|biryani|pulao|khichdi|upma", "food_grains"), (r"noodle|pasta|maggi|ramen|hakka", "bowl_chopsticks"),
             (r"roti|paratha|bread|toast|sandwich|dosa|chapati", "food_toast"), (r"pizza", "food_pizza"), (r"cake|sweet|dessert|kheer|halwa", "food_cake"),
             (r"coffee|tea|chai", "drink_coffee"), (r"fruit|apple|banana", "food_apple")]
def chip_icon(name):
    t = name.lower()
    hits = [(re.search(p, t).start(), i) for p, i in CHIP_ICON if re.search(p, t)]
    return min(hits)[1] if hits else "food"
CUISINE_ICON = [(r"kerala|south|tamil|andhra|udupi|karnataka|chettinad|coastal|goan", "leaf_one"),
                (r"chinese|thai|japanese|korean|asian|tibetan|burmese|momo", "bowl_chopsticks"),
                (r"italian|pizza", "food_pizza"), (r"bengali|fish", "food_fish"), (r"continental|western|american|mediterranean|mexican", "food"),
                (r"north|punjabi|mughlai|rajasthani|gujarati|maharashtrian|kashmiri|bihari", "food_toast"), (r"street|chaat", "food_grains")]
def cuisine_icon(c):
    if c.get("icon"): return c["icon"]
    for p, i in CUISINE_ICON:
        if re.search(p, c["name"].lower()): return i
    return "food"

# ---------- CSS ----------
CSS = r'''
:root{
  --base:#ECE9E4;--ink:#1C1A17;--ink2:#46423C;--mut:#5C5851;
  --w:#FFFFFF;--w2:rgba(255,255,255,.9);--w3:rgba(255,255,255,.78);
  --acc:#A96ADD;--acc-ink:#6E33A6;--acc-fill:#BE95E2;
  --lilac:#C599EC;--lilac-chip:#BE95E2;   /* Figma 199:463: icon boxes, "Often" chips */
  --gl-l:rgba(245,246,242,.88);--gl-d:rgba(30,25,19,.52);
  --hair-l:rgba(28,26,23,.08);--hair-d:rgba(255,255,255,.14);
  --nonveg:#8D3B1F;--veg:#1F6A25;--egg:#8A5A0A;
  --r:24px;--r-in:16px;--r-ic:12px;--fade:256px;--ease:cubic-bezier(.22,1,.36,1);
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--base);color:var(--ink);font-family:"Figtree",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;font-size:15px;line-height:22px;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.page{position:relative;max-width:440px;margin:0 auto;overflow:hidden;isolation:isolate;background:var(--base)}
img{display:block}
.i{display:block;flex:none}
.display{font-size:34px;line-height:38px;font-weight:600;letter-spacing:-.03em;margin:0}
h2{font-size:28px;line-height:32px;font-weight:600;letter-spacing:-.02em;margin:0}
.ttl{font-size:20px;line-height:26px;font-weight:600;letter-spacing:-.01em;margin:0}
.sum{margin:6px 0 0;color:var(--ink2)}
.head .sum{color:var(--ink)}
.t17{font-size:17px;line-height:22px;font-weight:600}
.s13{font-size:13px;line-height:18px;color:var(--mut)}
.lab{font-size:12px;line-height:16px;font-weight:500;color:var(--mut);margin:0}

/* sections, each on its own blurred background that crossfades into the next */
.sc{position:relative;padding:44px 16px}
.bgl{position:absolute;left:0;right:0;top:calc(var(--fade) / -2);bottom:calc(var(--fade) / -2);z-index:-1;pointer-events:none;background:var(--img) center/100% 100% no-repeat;
  -webkit-mask-image:linear-gradient(transparent,#000 var(--fade));mask-image:linear-gradient(transparent,#000 var(--fade))}
.bgl::after{content:"";position:absolute;inset:0;background:var(--wash,transparent)}
.sc.end .bgl{bottom:0;-webkit-mask-image:linear-gradient(transparent,#000 var(--fade),#000 calc(100% - 160px),transparent);mask-image:linear-gradient(transparent,#000 var(--fade),#000 calc(100% - 160px),transparent)}
.head{padding:0 4px 16px}
.sc.dk .head h2,.sc.dk .head .sum{color:var(--w)}
.stack > * + *{margin-top:16px}

/* the two glasses */
.gl{border-radius:var(--r);padding:20px;-webkit-backdrop-filter:blur(28px) saturate(1.5);backdrop-filter:blur(28px) saturate(1.5)}
.gl.l{background:var(--gl-l);color:var(--ink);box-shadow:inset 0 1px 0 rgba(255,255,255,.7),0 1px 2px rgba(20,16,12,.04),0 12px 32px rgba(20,16,12,.06)}
.gl.d{background:var(--gl-d);color:var(--w);-webkit-backdrop-filter:blur(28px) saturate(1.6) brightness(.94);backdrop-filter:blur(28px) saturate(1.6) brightness(.94);box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 12px 32px rgba(20,16,12,.08)}
.gl.d .lab,.gl.d .s13{color:var(--w3)}

/* small parts */
.ib{width:36px;height:36px;border-radius:var(--r-ic);background:rgba(255,255,255,.66);display:grid;place-items:center;color:var(--ink2);flex:none}
.pill{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:12px;font-size:12px;font-weight:600;white-space:nowrap;background:var(--acc-fill);color:#fff}
.pill.n{background:rgba(28,26,23,.06);color:var(--ink2);font-weight:500}
.pill.al{background:rgba(180,35,24,.1);color:#A3201A;font-weight:600}
.diet{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:500;color:var(--nonveg)}
.diet.vg{color:var(--veg)}.diet.eg{color:var(--egg)}
.mark{width:12px;height:12px;border:1.5px solid currentColor;border-radius:2px;display:grid;place-items:center}
.mark i{width:0;height:0;border-left:3px solid transparent;border-right:3px solid transparent;border-bottom:5px solid currentColor}
.diet.vg .mark i,.diet.eg .mark i{width:6px;height:6px;border:0;border-radius:50%;background:currentColor}
.ava{border-radius:50%;object-fit:cover;flex:none}

/* hero */
.hero{padding-top:0}
.hero .bgl{top:0;-webkit-mask-image:none;mask-image:none}
.photo{position:relative;margin:0 -16px;height:380px;overflow:hidden;-webkit-mask-image:linear-gradient(#000 50%,transparent 96%);mask-image:linear-gradient(#000 50%,transparent 96%)}
.photo img{width:100%;height:100%;object-fit:cover;object-position:50% 38%;filter:blur(7.5px);transform:scale(1.115)}
.photo::before{content:"";position:absolute;inset:0 0 auto;height:132px;background:linear-gradient(rgba(26,20,14,.46),rgba(26,20,14,.18) 55%,transparent);z-index:1}
.bar{position:absolute;top:30px;left:24px;right:24px;z-index:2;display:flex;align-items:center;justify-content:space-between}
.bar svg{display:block;opacity:.9}
.bar .tag{font-size:12px;line-height:14px;font-weight:500;color:#fff;text-shadow:0 1px 8px rgba(26,20,14,.35)}
.hg{position:relative;margin-top:-21px;padding:0 4px}
.hava{display:flex;margin-bottom:4px}
.hava .ava + .ava{margin-left:-20px}
.hg .greet{color:var(--ink)}
.hg h1{margin-top:4px;color:rgba(28,26,23,.56)}
.hg.m .display{font-size:30px;line-height:34px}
.hg.s .display{font-size:27px;line-height:31px}
.intro{margin-top:24px}
.intro p{margin:0}
.intro .k{font-size:13px;line-height:18px;color:rgba(35,34,34,.5)}
.intro .big{margin-top:8px;font-size:20px;line-height:27px;font-weight:600;letter-spacing:-.01em;color:#232222}
.intro.m .big{font-size:18px;line-height:25px}
.intro.s .big{font-size:17px;line-height:24px}
.intro .s{margin-top:8px;font-size:13px;line-height:18px;color:#232222}

/* household: 1 to 4 people */
.hh > * + *{margin-top:8px}
.hb{border-radius:20px;padding:16px}
.ppl{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.per{display:flex;flex-direction:column;gap:12px}
.per .nm{font-size:17px;line-height:22px;font-weight:600}
.per .sb{margin-top:2px;font-size:13px;line-height:18px;color:rgba(255,255,255,.7)}
.per .hr{height:1px;background:rgba(255,255,255,.12)}
.per .lk{font-size:12px;line-height:16px;font-weight:500;color:rgba(255,255,255,.7)}
.per .v{margin-top:2px;font-size:15px;line-height:22px;font-weight:500}
.per.w{grid-column:1/-1;display:grid;grid-template-columns:64px 1fr;column-gap:16px;row-gap:12px;align-items:center}
.per.w .hr,.per.w .lkb{grid-column:1/-1}
.hb .chips{margin-top:12px}
.hb .lab.w{color:#fff}
.chip.d{height:32px;padding:0 12px 0 10px;border-radius:16px;background:rgba(255,255,255,.14);color:#fff;box-shadow:none}
.chip.d .i{color:#fff}
.plat{display:grid;gap:6px;margin-top:12px}
.plat span{height:41px;border-radius:8px;background:#fff;box-shadow:inset 0 0 0 1px #E7E5E1;display:grid;place-items:center;padding:0 3px}
.plat img.sq{width:30px;height:30px;border-radius:6.6px}
.plat img.mk{max-width:47px;max-height:23px;object-fit:contain}
.plat img.mq{max-width:30px;max-height:30px;object-fit:contain}
.tx{font-weight:600;color:var(--ink);text-align:center;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* must-haves and no-gos: light glass for what is wanted, dark glass for what is not */
.rcs > * + *{margin-top:8px}
.rc{border-radius:var(--r);padding:20px;background:var(--gl-l);color:var(--ink);-webkit-backdrop-filter:blur(28px) saturate(1.5);backdrop-filter:blur(28px) saturate(1.5);box-shadow:inset 0 1px 0 rgba(255,255,255,.7),0 1px 2px rgba(20,16,12,.04),0 12px 32px rgba(20,16,12,.06)}
.rc.n{padding:20px 16px 12px;background:rgba(30,25,19,var(--nt,.4));color:#fff;-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);box-shadow:inset 0 1px 0 rgba(255,255,255,.14)}
.rc .hd{display:flex;align-items:center;gap:10px;padding-bottom:8px}
.rc .bdg{width:24px;height:24px;border-radius:12px;display:grid;place-items:center;flex:none;background:#2E7D32;color:#fff}
.rc.n .bdg{background:#FF8A7A;color:#2A140F}
.rc .hd b{flex:1;min-width:0;font-size:17px;line-height:22px;font-weight:600}
.rc ul{list-style:none;margin:0;padding:0}
.rc li{display:flex;align-items:flex-start;gap:12px;padding:10px 0}
.rc .mk{width:20px;height:20px;border-radius:10px;display:grid;place-items:center;flex:none;background:rgba(255,255,255,.75);color:#2E7D32;margin-top:1px}
.rc.n .mk{background:rgba(255,176,163,.2);color:#FFB0A3}
.rc li .t{flex:1;min-width:0}
.rc li .s13{display:block;margin-top:2px;color:var(--mut)}
.rc.n li .s13{color:rgba(255,255,255,.7)}
.apps{display:flex;flex-wrap:wrap;gap:10px;padding:8px 0 4px 32px}
.apt{position:relative;flex:none;width:84px;height:52px;border-radius:10px;background:#fff;box-shadow:inset 0 0 0 1px #E7E5E1;display:grid;place-items:center;padding:0 6px}
.rc.n .apt{border-radius:12px;box-shadow:none}
.apt img.sq{width:38px;height:38px;border-radius:8px}
.apt img.mk{max-width:66px;max-height:30px;object-fit:contain}
.apt img.mq{max-width:40px;max-height:38px;object-fit:contain}
.apt .x{position:absolute;right:-6px;top:-6px;width:20px;height:20px;border-radius:10px;background:#E5483F;color:#fff;display:grid;place-items:center}

/* rules of the house: a topic, then the one big fact */
.kr{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.kr .kt:last-child:nth-child(odd){grid-column:1/-1}
.kt{display:flex;flex-direction:column;gap:6px;min-height:148px;padding:16px;border-radius:20px;background:rgba(255,255,255,.9)}
.kt .top{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.kt .ib2{width:32px;height:32px;border-radius:8px;background:var(--lilac);display:grid;place-items:center;color:#fff;flex:none}
.kt .tp{font-size:13px;line-height:18px;font-weight:600;color:var(--mut)}
.kt b{font-size:28px;line-height:32px;font-weight:600;letter-spacing:-.84px;color:var(--ink)}
.kt p{margin:0;font-size:13px;line-height:18px;color:#56514A}

/* meals */
.meal{display:grid;grid-template-columns:72px 1fr;gap:16px;align-items:start}
.tile{width:72px;height:72px;border-radius:var(--r-in);background:rgba(255,255,255,.66);display:flex;align-items:center;justify-content:center}
.tile img{width:50px;height:50px;object-fit:contain}
.tile img + img{margin-left:-16px}
.tile.two img{width:42px;height:42px}
.meal .top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.meal .what{margin-top:6px;font-weight:500}
.meal .s13{margin-top:2px}
.each{display:flex;flex-direction:column;gap:6px;margin-top:12px}
.each span{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink2)}
.info{display:grid;grid-template-columns:36px 1fr;gap:12px;align-items:start}
.info .v{font-weight:500;margin-top:2px}
.info + .info{margin-top:16px}

/* food you love: cuisines, then the dishes */
.cu{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cu.odd .kt:first-child{grid-column:1/-1}
.cu .kt{min-height:0;gap:8px}
.cu .kt .ib2{width:32px;height:32px}
.cu.many .kt b{font-size:22px;line-height:26px;letter-spacing:-.4px}
.dish{display:flex;flex-direction:column;gap:16px}
.dg{display:flex;flex-direction:column;gap:12px}
.dg .gh{display:flex;justify-content:space-between;gap:8px;font-size:17px;line-height:22px;font-weight:600}
.dg .gh span{color:var(--ink)}
.dg.o .gh span{color:var(--acc)}
.dish .hr{height:1px;background:var(--hair-l)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 14px 0 12px;border-radius:18px;font-size:14px;font-weight:500;white-space:nowrap;background:rgba(255,255,255,.72);color:var(--ink);box-shadow:inset 0 0 0 1px rgba(28,26,23,.06)}
.chip .i{color:var(--mut)}
.chip.o{background:var(--lilac-chip);color:#fff;box-shadow:none;font-weight:600}
.chip.o .i{color:#fff}

/* spice and proteins */
.spice{padding:32px 20px 28px}
.gauge{position:relative;width:174px;height:87px;margin:0 auto}
.gauge svg{display:block}
.gauge .ch{position:absolute;left:0;right:0;top:40px;display:flex;justify-content:center}
.gauge .ch img{width:30px;height:30px}
.gauge .ch img + img{margin-left:-7px}
.gauge .ch .off{opacity:.38;filter:saturate(.45)}
.lvl{display:flex;justify-content:center;align-items:baseline;gap:32px;margin-top:12px}
.lvl span{font-size:15px;color:var(--mut)}
.lvl b{font-size:30px;line-height:36px;font-weight:600;letter-spacing:-.03em;color:var(--ink)}
.prot{padding:24px 16px 4px}
.prot .ttl{padding:0 0 16px}
.pr{display:grid;grid-template-columns:56px 1fr auto;gap:16px;align-items:center;min-height:68px;padding:8px 0;border-top:1px solid var(--hair-d)}
.pr .art{width:56px;height:48px;display:flex;align-items:center;justify-content:center}
.pr .art img{max-width:56px;max-height:46px;object-fit:contain}
.pr .art .ph{width:44px;height:44px;border-radius:22px;background:rgba(255,255,255,.14);display:grid;place-items:center;color:rgba(255,255,255,.8)}
.pr .nm{font-size:17px;line-height:22px;font-weight:500}
.pr .r{display:flex;flex-direction:column;align-items:flex-end;gap:8px}
.dots{display:inline-flex;gap:6px}
.dots i{width:11px;height:11px;border-radius:50%;background:rgba(255,255,255,.26)}
.dots i.on{background:#fff}
.pr .w{font-size:12px;line-height:16px;color:var(--w3)}

/* where your food comes from: one glass cabinet, one shelf per kind of food */
.sc.kit .bgl{background:var(--img) 50% 0/100% auto no-repeat,#F4EFE6}
.fridge{border-radius:20px;padding:8px;background:rgba(255,255,255,.25);-webkit-backdrop-filter:blur(50px);backdrop-filter:blur(50px)}
.door{background:rgba(255,255,255,.7);border-radius:20px;padding:20px 16px 20px 20px}
.door h2{font-size:22px;line-height:28px;letter-spacing:-.44px}
.door .sum{margin-top:4px;color:#56514A}
.cab{margin-top:8px;background:rgba(255,255,255,.7);border-radius:20px;padding:0 16px 4px}
.shelf{display:flex;flex-direction:column;gap:12px;padding:16px 0 14px}
.shelf + .shelf{border-top:1px solid #fff}
.lr{display:flex;align-items:center;justify-content:space-between;gap:8px}
.fp{border-radius:999px;padding:3px 8px;background:linear-gradient(135deg,#EBF0FF,#F2ECFF);box-shadow:inset 0 0 0 1px #D3DBFA;font-size:12px;line-height:16px;font-weight:500;color:#3A4FC0;white-space:nowrap}
.it{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:52px}
.pp{display:flex;align-items:flex-end;gap:4px}
.pp img{height:46px;width:auto;max-width:56px;object-fit:contain}
.pp.eggs img{width:40px;height:44px}
.pp.eggs img + img{margin-left:-14px}
.ap2{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:10px}
.ap2.c{gap:8px}.ap2.c .apt{width:70px;height:46px;border-radius:9px}.ap2.c img.sq{width:32px;height:32px;border-radius:7px}.ap2.c img.mk{max-width:56px;max-height:26px}.ap2.c img.mq{max-width:34px;max-height:32px}
.fas{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px}
.fa{display:flex;flex-direction:column;align-items:flex-start;gap:8px;padding:12px 16px 16px;border-radius:20px;background:linear-gradient(180deg,#fff 12%,rgba(169,106,221,.25));-webkit-backdrop-filter:blur(25px);backdrop-filter:blur(25px)}
.fa .ib2{width:32px;height:32px;border-radius:8px;background:var(--lilac);display:grid;place-items:center;color:#fff}
.fa b{font-size:17px;line-height:22px;font-weight:600}
.fa .d{margin:-4px 0 0;font-size:12px;line-height:16px;color:var(--mut)}
.fa .its{display:flex;flex-wrap:wrap;gap:6px;padding-top:4px}
.fa .its i{font-style:normal;padding:5px 10px;border-radius:14px;background:#F3F0EA;font-size:13px;line-height:18px;font-weight:500}
.fa.one{grid-column:1/-1}
.sub2{margin-top:44px}

/* people */
.pc .ph{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.pc .nm{font-size:17px;line-height:22px;font-weight:600}
.pc .rt{margin-left:auto}

/* closing */
.closing{padding-bottom:120px}
.closing .gl{padding:28px 24px}
.closing .mpill{display:inline-flex;margin-bottom:24px}
.closing .display{font-size:30px;line-height:34px}
.closing p{margin:12px 0 0;color:var(--ink2)}
.ask{display:flex;align-items:center;gap:16px;margin-top:16px;background:rgba(30,25,19,.62);color:#fff;border-radius:var(--r);padding:20px;text-decoration:none;-webkit-backdrop-filter:blur(28px) saturate(1.4);backdrop-filter:blur(28px) saturate(1.4);box-shadow:inset 0 1px 0 rgba(255,255,255,.18)}
.ask .go{margin-left:auto;width:36px;height:36px;border-radius:18px;background:rgba(255,255,255,.18);display:grid;place-items:center;flex:none}
.ask:focus-visible{outline:2px solid var(--acc);outline-offset:3px}

/* one entrance */
.js .rv{opacity:0;transform:translateY(10px);transition:opacity .4s var(--ease),transform .4s var(--ease)}
.js .rv.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.js .rv{opacity:1;transform:none;transition:none}}
'''

S = []
H = data["hero"]
people = data["people"]

# 1 hero — the kitchen photo stays the same for every household
g_len = len(H["greeting"])
g_cls = "" if g_len <= 22 else ("m" if g_len <= 30 else "s")
about = H["about"]; b_len = len(about["big"])
a_cls = "" if b_len <= 80 else ("m" if b_len <= 120 else "s")
hero_img = asset("bg", os.path.join(LIB, "backgrounds", "hero-kitchen.jpg"))
S.append(f'''<header class="sc hero">{bg("ice-beige", "rgba(250,246,240,.18)")}
<div class="photo"><img src="{hero_img}" alt="" width="662" height="845" fetchpriority="high"><div class="bar">{M(92, "#fff")}<span class="tag">Household Profile</span></div></div>
<div class="hg {g_cls}"><div class="hava">{"".join(ava(p, 75) for p in people)}</div>
<p class="display greet">{e(H["greeting"])}</p><h1 class="display">{e(H["headline"])}</h1></div>
<div class="gl l intro {a_cls} rv"><p class="k">{e(about["label"])}</p><p class="big">{e(about["big"])}</p>{f'<p class="s">{e(about["small"])}</p>' if about.get("small") else ""}</div>
</header>''')

# 2 household
def sub_line(p):
    a = p.get("allergies", "No allergies")
    return f'{DIET.get(p["diet"], DIET["nonveg"])[0]}, {a[0].lower() + a[1:]}'
def per(p, wide=False):
    likes = f'<div class="lkb"><div class="lk">Likes</div><div class="v">{e(p["likes"])}</div></div>' if p.get("likes") else ""
    return (f'<div class="gl d hb per{" w" if wide else ""}">{ava(p, 64)}<div><div class="nm">{e(p["name"])}</div><div class="sb">{e(sub_line(p))}</div></div>'
            + (f'<div class="hr"></div>{likes}' if likes else "") + "</div>")
n = len(people)
cards = "".join(per(p, wide=(n == 1 or (n % 2 == 1 and i == n - 1))) for i, p in enumerate(people))
cuis = "".join(f'<span class="chip d">{fi(cuisine_icon(c), 16)}{e(c["name"])}</span>' for c in data["cuisines"])
pl = data.get("platforms", [])
cols = min(5, max(2, len(pl)))
plat = "".join(f"<span>{logo(x)}</span>" for x in pl)
HHd = data["household"]
S.append(f'''<section class="sc dk" aria-labelledby="home-h">{bg("beige-teal", "linear-gradient(rgba(36,28,20,.6),rgba(36,28,20,.42) 22%,rgba(36,28,20,.14) 55%,rgba(36,28,20,0) 85%)")}{head(HHd["title"], HHd.get("sub"), "home-h")}
<div class="hh"><div class="ppl rv">{cards}</div>
<div class="gl d hb rv"><p class="lab">Cuisines you come back to</p><div class="chips">{cuis}</div></div>
{f'<div class="gl d hb rv"><p class="lab w">Preferred Platforms</p><div class="plat" style="grid-template-columns:repeat({cols},1fr)">{plat}</div></div>' if pl else ""}</div>
</section>''')

# 3 meals — any number of meals; the picture is chosen from what is eaten
def tile(arts):
    return f'<div class="tile{" two" if len(arts) > 1 else ""}">{"".join(ill(a) for a in arts)}</div>'
def meal(m):
    arts = m.get("art") or art_for(m["what"] + " " + m.get("sub", ""), 2 if "salad" in m["what"].lower() else 1)
    if not m.get("art"): REPORT["auto_art"].append(f'{m["name"]}: {", ".join(arts) or "none"}')
    if not arts: arts = ["spice-box"]
    each = ""
    rows = [x for x in m.get("each", []) if x["person"] in PEOPLE]
    REPORT.setdefault("unknown_people", []).extend(x["person"] for x in m.get("each", []) if x["person"] not in PEOPLE)
    if rows:
        each = '<div class="each">' + "".join(f'<span>{ava(PEOPLE[x["person"]], 24)}{e(x["text"])}</span>' for x in rows) + "</div>"
    tag = f'<span class="pill n">{e(m["tag"])}</span>' if m.get("tag") else ""
    return (f'<div class="gl l meal rv">{tile(arts)}<div><div class="top"><span class="t17">{e(m["name"])}</span>{tag}</div>'
            f'<div class="what">{e(m["what"])}</div>{f"<div class=s13>{e(m[chr(115)+chr(117)+chr(98)])}</div>" if m.get("sub") else ""}{each}</div></div>')
def note(m):
    arts = m.get("art") or art_for(m["what"] + " " + m.get("sub", ""), 1)
    if not m.get("art"): REPORT["auto_art"].append(f'{m["label"]}: {", ".join(arts) or "none"}')
    arts = arts or ["spice-box"]
    return (f'<div class="gl l meal rv">{tile(arts)}<div><p class="lab">{e(m["label"])}</p><div class="what" style="margin-top:2px">{e(m["what"])}</div>'
            f'{f"<div class=s13>{e(m[chr(115)+chr(117)+chr(98)])}</div>" if m.get("sub") else ""}</div></div>')
MD = data["meals"]
S.append(f'''<section class="sc dk" aria-labelledby="meals-h">{bg("green-teal", "linear-gradient(rgba(36,28,20,.5),rgba(36,28,20,.4) 260px,rgba(36,28,20,0) 560px),linear-gradient(rgba(250,248,244,.16),rgba(250,248,244,.16))")}{head(MD["title"], MD.get("sub"), "meals-h")}<div class="stack">
{"".join(meal(m) for m in MD["items"])}{"".join(note(m) for m in MD.get("notes", []))}
{pair(MD.get("must"), MD.get("nogo"))}
</div></section>''')

# 4 food you love — 1 to 6 cuisines; odd counts lead with one wide tile
def kc(c): return f'<div class="kt"><span class="ib2">{fi(cuisine_icon(c), 18)}</span><b>{e(c["name"])}</b>{f"<p>{e(c[chr(110)+chr(111)+chr(116)+chr(101)])}</p>" if c.get("note") else ""}</div>'
def dg(name, items, often):
    chips = "".join(f'<span class="chip{" o" if often else ""}">{fi(chip_icon(x), 16)}{e(x)}</span>' for x in items)
    return f'<div class="dg{" o" if often else ""}"><div class="gh">{name}<span>{len(items)}</span></div><div class="chips">{chips}</div></div>'
LV = data["love"]; cu = data["cuisines"]
groups = [dg("Often", LV["often"], True)] if LV.get("often") else []
if LV.get("later"): groups.append(dg("Now and then", LV["later"], False))
S.append(f'''<section class="sc dk" aria-labelledby="love-h">{bg("crimson-blue", "rgba(20,24,40,.16)")}{head(LV["title"], LV.get("sub"), "love-h")}
<div class="stack"><div class="cu{" odd" if len(cu) % 2 else ""}{" many" if len(cu) >= 4 else ""} rv">{"".join(kc(c) for c in cu)}</div>
{f'<div class="gl l dish rv">{chr(10).join([groups[0]] + ([chr(60)+"div class=hr"+chr(62)+chr(60)+"/div"+chr(62)] if len(groups) > 1 else []) + groups[1:])}</div>' if groups else ""}</div></section>''')

# 5 spice and proteins — no heading, as in Figma
def gauge(level):
    r, cx, cy, gap = 75, 87, 81, 14; seg = (180 - gap * 2) / 3
    pt = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    out = ""
    for k in range(3):
        col = "#F5A93A" if k < level else "rgba(28,26,23,.14)"
        a0 = 180 + k * (seg + gap); (x0, y0), (x1, y1) = pt(a0), pt(a0 + seg)
        out += f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}" stroke="{col}" stroke-width="12" stroke-linecap="round" fill="none"/>'
    return f'<svg width="174" height="87" viewBox="0 0 174 87" aria-hidden="true">{out}</svg>'
def prot_art(name):
    a = (art_for(name, 1) or [None])[0]
    if a is None and not any(name in x for x in REPORT["missing_art"]): REPORT["missing_art"].append(f"{name} (not in the ingredient index)")
    return "eggs" if a == "egg-fresh" else a   # proteins show the egg carton
def prow(p):
    a = prot_art(p["name"])
    art = ill(a) if a else f'<span class="ph" title="No picture yet">{fi("food", 22)}</span>'
    return f'<div class="pr"><span class="art">{art}</span><span class="nm">{e(p["name"])}</span><span class="r">{dots(p["freq"])}<span class="w">{e(p["label"])}</span></span></div>'
lvl = data.get("spice", {}).get("level")
spice = ""
if lvl:
    LVL = {1: "Mild", 2: "Medium", 3: "Hot"}[lvl]
    chil = "".join(ill("chilli", "" if k < lvl else "off") for k in range(3))
    spice = (f'<div class="gl l spice rv" role="img" aria-label="Spice level: {LVL.lower()}"><div class="gauge">{gauge(lvl)}<div class="ch">{chil}</div></div>'
             f'<div class="lvl"><span>Mild</span><b>{LVL}</b><span>Hot</span></div></div>')
prows = "".join(prow(p) for p in data.get("proteins", []))
if spice or prows:
    S.append(f'''<section class="sc dk" aria-label="Spice and proteins">{bg("gold-black", "rgba(20,16,10,.2)")}<div class="stack">
{spice}{f'<div class="gl d prot rv"><p class="ttl">Your favourite proteins</p>{prows}</div>' if prows else ""}
</div></section>''')

# 6 where your food comes from — default shelves: chicken, seafood, eggs, fresh food and veggies
SHELF = {"chicken": ("Chicken", ["roast-chicken"]), "seafood": ("Seafood", ["fish", "shrimp"]), "eggs": ("Eggs", ["egg-fresh"] * 3),
         "fresh": ("Fresh food and veggies", ["tomato-fresh", "spinach", "carrot"]), "mutton": ("Mutton", ["lamb-chops"]),
         "dairy": ("Dairy", ["milk", "yogurt"]), "bakery": ("Bread and bakery", ["bread-fresh"])}
ORDER = check.SHELVES   # chicken, seafood, eggs, fresh, then mutton, dairy, bakery
SD = data["sources"]
gs = sorted(SD["groups"], key=lambda g: ORDER.index(g["kind"]) if g["kind"] in ORDER else 9)
def shelf(g):
    title, arts = SHELF.get(g["kind"], (g.get("title", g["kind"].title()), []))
    title = g.get("title", title)
    if g.get("items"):
        picked = []
        for x in g["items"]:
            a = (art_for(x, 1) or [None])[0]
            if a and a not in picked: picked.append(a)
        if picked: arts = picked[:3]
    note = f'<span class="fp">{e(g["note"])}</span>' if g.get("note") else ""
    na = len(g.get("apps", []))
    if g["kind"] != "eggs": arts = arts[:max(1, min(3, (318 - na * 94) // 60))]  # leave the apps room on one line
    elif na >= 3: arts = arts[:2]
    apps = "".join(f'<span class="apt">{logo(x, "app")}</span>' for x in g.get("apps", []))
    if na >= 3: apps = f'<span class="ap2 c">{apps}</span>'
    elif apps: apps = f'<span class="ap2">{apps}</span>'
    pics = f'<span class="pp{" eggs" if g["kind"] == "eggs" else ""}">{"".join(ill(a) for a in arts)}</span>'
    return f'<div class="shelf"><div class="lr"><span class="t17">{e(title)}</span>{note}</div><div class="it">{pics}{apps}</div></div>'
def fa(icon, title, desc, items, one=False):
    return f'<div class="fa{" one" if one else ""}"><span class="ib2">{fi(icon, 18)}</span><b>{title}</b><p class="d">{desc}</p><span class="its">{"".join(f"<i>{e(x)}</i>" for x in items)}</span></div>'
fas = []
if SD.get("filler"): fas.append(("vehicle_truck_profile", "Filler items", "Added to your cart to meet the minimum cart value", SD["filler"]))
if SD.get("stock"): fas.append(("home", "Always in stock", "Kept available at all times", SD["stock"]))
FAS = f'<div class="fas rv">{"".join(fa(*x, one=len(fas) == 1) for x in fas)}</div>' if fas else ""
KD = data.get("kitchen")
kitchen = ""
if KD:
    xapps = ""
    if KD.get("nogo_apps"):
        xapps = '<div class="apps">' + "".join(f'<span class="apt">{logo(x, "app")}<span class="x">{fi("dismiss_12f", 10, "")}</span></span>' for x in KD["nogo_apps"]) + "</div>"
    kitchen = f'<div class="sub2">{head(KD["title"], KD.get("sub"), "buy-h")}{pair(KD.get("must"), KD.get("nogo"), xapps, nt=".72")}</div>'
S.append(f'''<section class="sc kit" aria-labelledby="food-h">{bg("kitchen", "linear-gradient(transparent 497px,#F4EFE6 906px)")}
<div class="fridge rv"><div class="door"><h2 id="food-h">{e(SD["title"])}</h2>{f"<p class=sum>{e(SD[chr(115)+chr(117)+chr(98)])}</p>" if SD.get("sub") else ""}</div>
<div class="cab">{"".join(shelf(g) for g in gs)}</div></div>
{FAS}{kitchen}
</section>''')

# 7 the little thing we noticed — one card per person who has something of their own
def info(r):
    s = f'<div class="s13">{e(r["sub"])}</div>' if r.get("sub") else ""
    return f'<div class="info"><span class="ib">{fi(r.get("icon", "star"), 18)}</span><div><p class="lab">{e(r["label"])}</p><div class="v">{e(r["value"])}</div>{s}</div></div>'
def pcard(p):
    a = p.get("allergies", "No allergies")
    pill = f'<span class="rt pill {"n" if a.lower().startswith("no ") else "al"}">{e(a)}</span>'
    return f'<div class="gl l pc rv"><div class="ph">{ava(p, 72)}<div><div class="nm">{e(p["name"])}</div>{diet(p["diet"])}</div>{pill}</div>{"".join(info(r) for r in p["noticed"])}</div>'
ND = data["noticed"]
pcs = "".join(pcard(p) for p in people if p.get("noticed"))
if pcs:
    S.append(f'''<section class="sc dk" aria-labelledby="one-h">{bg("green-black", "linear-gradient(rgba(36,28,20,.6),rgba(36,28,20,.45) 260px,rgba(36,28,20,0) 560px),linear-gradient(rgba(250,248,244,.1),rgba(250,248,244,.1))")}{head(ND["title"], ND.get("sub"), "one-h")}<div class="stack">{pcs}</div></section>''')

# 8 rules of the house — every tile says what it is about before the number
RD = data["rules"]
def kt(f): return f'<div class="kt"><div class="top"><span class="ib2">{fi(f.get("icon", "star"), 18)}</span><span class="tp">{e(f["topic"])}</span></div><b>{e(f["value"])}</b><p>{e(f["sub"])}</p></div>'
S.append(f'''<section class="sc dk" aria-labelledby="rules-h">{bg("green-teal", "linear-gradient(rgba(36,28,20,.5),rgba(36,28,20,.4) 260px,rgba(36,28,20,0) 560px),linear-gradient(rgba(250,248,244,.16),rgba(250,248,244,.16))")}{head(RD["title"], RD.get("sub"), "rules-h")}<div class="stack">
{f'<div class="kr rv">{"".join(kt(f) for f in RD["facts"])}</div>' if RD.get("facts") else ""}
{pair(RD.get("must"), RD.get("nogo"))}
</div></section>''')

# 9 closing
CD = data["closing"]
S.append(f'''<section class="sc end closing" aria-labelledby="end-h">{bg("blue-pink")}<div class="gl l rv">
<span class="mpill">{M(88)}</span><h2 id="end-h" class="display">{e(CD["title"])}</h2><p>{e(CD["text"])}</p></div>
<a class="ask rv" href="#"><span class="t17">{e(CD["cta"])}</span><span class="go">{fi("arrow_right", 18)}</span></a></section>''')

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(data["title"])} · Household profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&display=swap" rel="stylesheet">
<script>document.documentElement.classList.add("js")</script>
<style>{CSS}</style></head><body><div class="page">{"".join(S)}</div>
<script>
const els=[...document.querySelectorAll(".rv")];
if(location.hash=="#all")els.forEach(el=>el.classList.add("in"));else if("IntersectionObserver" in window){{const io=new IntersectionObserver(es=>{{es.forEach(e=>{{if(!e.isIntersecting)return;e.target.classList.add("in");io.unobserve(e.target)}})}},{{rootMargin:"0px 0px -6% 0px"}});els.forEach(el=>io.observe(el))}}else els.forEach(el=>el.classList.add("in"));
</script></body></html>'''

os.makedirs(OUT, exist_ok=True)
if os.path.isdir(os.path.join(OUT, "assets")): shutil.rmtree(os.path.join(OUT, "assets"))
for rel, src in COPY.items():
    dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
out_html = os.path.join(OUT, f"household-{SLUG}.html")
open(out_html, "w").write(page)
REPORT["missing_art"] = sorted(set(REPORT["missing_art"]))
REPORT["stand_ins"] = sorted(set(REPORT["stand_ins"]))
json.dump(REPORT, open(os.path.join(OUT, "report.json"), "w"), indent=1, ensure_ascii=False)
print(out_html)
print("assets:", len(COPY), "| no picture:", REPORT["missing_art"] or "none", "| text logos:", REPORT["text_logos"] or "none")
print("stand-ins:", REPORT["stand_ins"] or "none")
print("auto-picked meal art:", "; ".join(REPORT["auto_art"]))
