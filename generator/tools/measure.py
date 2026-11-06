# Measure the real rendered contrast of every line of text on a built household page.
# usage: python3 measure.py <html path> [width]
# Run 1 dumps text line boxes + computed colours via --dump-dom, run 2 screenshots the page,
# then each line's background is taken as the median pixel of its own line box.
import sys, os, json, subprocess, struct, re, html as H
C = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
src = os.path.abspath(sys.argv[1]); W = int(sys.argv[2]) if len(sys.argv) > 2 else 390
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp"); os.makedirs(D, exist_ok=True); base = "file://" + os.path.dirname(src).replace(" ", "%20") + "/"
raw = open(src).read()
COLLECT = r'''<script>
addEventListener("load",()=>document.fonts.ready.then(()=>setTimeout(()=>{
 const out=[],over=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
 const sy=scrollY;
 while(n=w.nextNode()){if(!n.data.trim())continue;const el=n.parentElement;if(el.closest("script,style"))continue;
  const cs=getComputedStyle(el);let op=1;for(let e=el;e;e=e.parentElement)op*=+getComputedStyle(e).opacity;
  const r=document.createRange();r.selectNodeContents(n);
  const box=el.closest(".kt,.fa,.apt,.plat>span,.rc,.gl,.door,.cab,.page");const bb=box.getBoundingClientRect();
  for(const b of r.getClientRects()){if(b.width<2||b.height<2)continue;
   if(b.right>bb.right+1||b.left<bb.left-1)over.push({t:n.data.trim().slice(0,60),cls:box.className,y:b.top+sy,by:Math.round(b.right-bb.right)});
   out.push({t:n.data.trim().slice(0,48),cls:(el.className&&el.className.baseVal===undefined?el.className:"")||el.tagName,
   col:cs.color,fs:parseFloat(cs.fontSize),fw:+cs.fontWeight,op,x:b.left,y:b.top+sy,w:b.width,h:b.height})}}
 for(const a of document.querySelectorAll(".ap2")){const tops=new Set([...a.children].map(c=>Math.round(c.getBoundingClientRect().top)));if(tops.size>1){const sh=a.closest(".shelf");over.push({t:"Too many apps on the "+sh.querySelector(".t17").textContent+" shelf: they wrap to a second row (a shelf fits 3)",cls:"shelf",y:a.getBoundingClientRect().top+sy,by:0})}}
 document.body.innerHTML="<pre id=OUT>"+JSON.stringify({h:Math.ceil(document.querySelector(".page").getBoundingClientRect().height),items:out,over})+"</pre>";
},1500)));
</script>'''
inj = raw.replace("<head>", f'<head><base href="{base}">', 1).replace("</style>", f".page{{width:{W}px;max-width:none;margin:0}}</style>", 1)  # headless has a minimum window width; pin the phone width
m1 = os.path.join(D, "_m1.html"); m2 = os.path.join(D, "_m2.html")
open(m1, "w").write(inj.replace("</body>", COLLECT + "</body>"))
open(m2, "w").write(inj)
def chrome(args, url, h):
    return subprocess.run([C, "--headless=new", "--hide-scrollbars", f"--window-size={W},{h}", "--virtual-time-budget=6000", *args, url],
                          capture_output=True, text=True).stdout
# first pass with a tall window so no viewport-height effects differ between runs
dom = chrome(["--dump-dom"], "file://" + m1 + "#all", 9000)
data = json.loads(H.unescape(re.search(r'<pre id="?OUT"?>(.*?)</pre>', dom, re.S).group(1)))
PH = data["h"]
png = os.path.join(D, "_shot.png"); bmp = os.path.join(D, "_shot.bmp")
chrome([f"--screenshot={png}"], "file://" + m2 + "#all", 9000)
subprocess.run(["sips", "-s", "format", "bmp", png, "--out", bmp], capture_output=True)
b = open(bmp, "rb").read()
off = struct.unpack_from("<I", b, 10)[0]; bw, bh = struct.unpack_from("<ii", b, 18); bpp = struct.unpack_from("<H", b, 28)[0] // 8
stride = (bw * bpp + 3) & ~3; top_down = bh < 0; bh = abs(bh)
def px(x, y):
    if not (0 <= x < bw and 0 <= y < bh): return None
    row = y if top_down else bh - 1 - y
    i = off + row * stride + x * bpp
    return (b[i + 2], b[i + 1], b[i])
def lin(c): c /= 255; return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
def L(c): return .2126 * lin(c[0]) + .7152 * lin(c[1]) + .0722 * lin(c[2])
def cr(a, b): la, lb = sorted((L(a), L(b)), reverse=True); return (la + .05) / (lb + .05)
def parse(col):
    v = [float(x) for x in re.findall(r"[\d.]+", col)]
    return v[:3], (v[3] if len(v) > 3 else 1)
rows = []
for it in data["items"]:
    x0, y0 = int(it["x"]), int(it["y"]); x1, y1 = int(it["x"] + it["w"]), int(it["y"] + it["h"])
    ps = [p for yy in range(y0, y1, 1) for xx in range(x0, x1, 2) if (p := px(xx, yy))]
    if not ps: continue
    rgb, a = parse(it["col"]); a *= it["op"]
    ps.sort(key=L)
    # pixels furthest from the text colour are background; take the median of the far half
    tl = L(rgb); far = ps[len(ps)//2:] if tl < L(ps[len(ps)//2]) else ps[:len(ps)//2 + 1]
    bg = far[len(far)//2]
    worst = far[len(far)//10] if tl < L(bg) else far[-1 - len(far)//10]
    txt = [rgb[k] * a + bg[k] * (1 - a) for k in range(3)]
    big = it["fs"] >= 24 or (it["fs"] >= 18.66 and it["fw"] >= 600)
    need = 3 if big else 4.5
    rows.append((it["y"], it["t"], it["cls"], it["fs"], it["fw"], round(cr(txt, bg), 2), round(cr(txt, worst), 2), need, "#%02x%02x%02x" % tuple(bg)))
show_all = "--all" in sys.argv
print(f"page height {PH}px, {len(rows)} line boxes")
for o in data.get("over", []):   # text that runs past the edge of its card, chip or tile
    print(f"OVERFLOW {int(o['y']):5d}  {o['by']:+d}px past [{str(o['cls'])[:18]}] {o['t']}")
for y, t, cls, fs, fw, c, cw, need, bg in rows:
    flag = "FAIL" if c < need else ("weak" if cw < need else "")
    if show_all or flag:
        print(f"{int(y):5d}  {flag:4s} {c:5.2f} (worst {cw:5.2f}) need {need}  {fs:.0f}/{fw}  bg {bg}  [{str(cls)[:18]}] {t}")
