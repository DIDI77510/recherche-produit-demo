#!/usr/bin/env python3
"""Génère les 4 slides PNG (1080x1440) d'un carrousel à partir d'un fichier JSON.

Usage : python3 tools/build.py posts/<dossier>/content.json
Les PNG sont écrits à côté du JSON (slide-1.png ... slide-4.png).
Le script échoue si un texte déborde : raccourcir le texte et relancer.
"""
import json, os, subprocess, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
BG, FG, MUTED, CARD = "#0B0B0B", "#FAF6F0", "#E6E0D8", "#1A1A1A"

def e(s):
    return html.escape(str(s), quote=False)

def page(body, accent, handle, num):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@font-face{{font-family:'Anton';src:url('file://{FONTS}/anton-latin-400-normal.woff2')}}
@font-face{{font-family:'DM Sans';font-weight:400;src:url('file://{FONTS}/dm-sans-latin-400-normal.woff2')}}
@font-face{{font-family:'DM Sans';font-weight:500 700;src:url('file://{FONTS}/dm-sans-latin-700-normal.woff2')}}
body{{margin:0}}
.a{{font-family:'Anton',sans-serif}} .ac{{color:{accent}}}
</style></head><body>
<div id="root" style="width:1080px;height:1440px;box-sizing:border-box;padding:72px 72px 40px;background:{BG};color:{FG};display:flex;flex-direction:column;font-family:'DM Sans',sans-serif;overflow:hidden">
<div id="content" style="display:flex;flex-direction:column">{body}</div>
<div id="foot" style="margin-top:auto;display:flex;justify-content:space-between;border-top:2px solid #3A3A3A;padding-top:22px;font-size:30px;color:#CFC8BF"><span>{e(handle)}</span><span>0{num} / 04</span></div>
</div></body></html>"""

def kicker(text, accent, pill=False):
    if pill:
        return f'<div class="a" style="align-self:flex-start;background:{accent};color:{BG};border-radius:10px;padding:8px 20px;font-size:40px;letter-spacing:2px">{e(text)}</div>'
    return f'<div class="a ac" style="display:flex;align-items:center;gap:20px;font-size:40px;letter-spacing:4px">{e(text)}<span style="display:block;width:90px;height:4px;background:{accent}"></span></div>'

def title(l1, l2, size):
    return (f'<div class="a" style="margin-top:28px;font-size:{size}px;line-height:0.95;text-transform:uppercase">{e(l1)}</div>'
            f'<div class="a ac" style="font-size:{size}px;line-height:0.95;text-transform:uppercase">{e(l2)}</div>')

def cta(text):
    return f'<div class="a" style="margin-top:28px;font-size:44px;letter-spacing:2px;text-align:center">{e(text)} →</div>'

def slide1(s, accent):
    lines = "".join(f'<div class="a" style="font-size:{s.get("lines_size",140)}px;line-height:0.95;text-transform:uppercase">{e(l)}</div>' for l in s["lines"])
    return (kicker(s["kicker"], accent)
        + (f'<div class="a" style="margin-top:36px;font-size:120px;line-height:0.95;text-transform:uppercase">{e(s["pre"])}</div>' if s.get("pre") else '<div style="height:36px"></div>')
        + f'<div class="a ac" style="font-size:{s.get("big_size",300)}px;line-height:0.9">{e(s["big"])}</div>'
        + lines
        + f'<div class="a ac" style="font-size:{s.get("lines_size",140)}px;line-height:0.95;text-transform:uppercase">{e(s["accent_line"])}</div>'
        + f'<p style="margin:40px 0 0;font-size:42px;line-height:1.25;font-weight:700">{e(s["intro"])}</p>'
        + f'<div class="a" style="margin-top:32px;border:4px solid {accent};border-radius:18px;padding:22px 32px;font-size:46px;text-transform:uppercase;text-align:center">{e(s["box"])}</div>'
        + f'<p style="margin:20px 0 0;font-size:30px;color:#CFC8BF;text-align:center">{e(s["note"])}</p>'
        + cta("ENREGISTRE ET FAIS DÉFILER"))

def slide2(s, accent):
    cards = "".join(
        f'<div style="display:flex;gap:30px;align-items:flex-start;background:{CARD};border-radius:20px;padding:26px 30px">'
        f'<div class="a ac" style="flex:none;width:200px;font-size:72px;line-height:1">{e(c["tag"])}</div>'
        f'<div><div class="a" style="font-size:48px;line-height:1.05;text-transform:uppercase">{e(c["title"])}</div>'
        f'<p style="margin:8px 0 0;font-size:31px;line-height:1.3;color:{MUTED}">{e(c["text"])}</p></div></div>'
        for c in s["cards"])
    return (kicker(s["kicker"], accent) + title(s["title1"], s["title2"], 130)
        + f'<div style="margin-top:36px;display:flex;flex-direction:column;gap:18px">{cards}</div>'
        + f'<div style="margin-top:20px;border:2px solid {accent};border-radius:20px;padding:20px 28px;font-size:30px;line-height:1.3;color:{MUTED}">⚠ {e(s["warn"])}</div>'
        + f'<p style="margin:16px 0 0;font-size:26px;color:#A8A198;text-align:center">{e(s["source"])}</p>'
        + cta("LA SUITE"))

def slide3(s, accent):
    items = "".join(
        f'<div style="display:flex;gap:32px;align-items:flex-start"><div class="a" style="flex:none;width:76px;height:76px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;font-size:44px">{i+1}</div>'
        f'<div><div style="font-size:42px;font-weight:700">{e(it["t"])}</div><p style="margin:6px 0 0;font-size:31px;line-height:1.3;color:{MUTED}">{e(it["d"])}</p></div></div>'
        for i, it in enumerate(s["items"]))
    return (kicker(s["kicker"], accent) + title(s["title1"], s["title2"], 135)
        + f'<div style="margin-top:36px;display:flex;flex-direction:column;gap:24px">{items}</div>'
        + f'<div class="a" style="margin-top:32px;background:{accent};color:{BG};border-radius:18px;padding:24px 32px;font-size:50px;line-height:1.1;text-align:center">{e(s["banner"])}</div>'
        + cta("OÙ TROUVER MON LIEN ?"))

def slide4(s, accent):
    items = "".join(
        f'<div style="display:flex;gap:26px;align-items:center"><span class="a ac" style="font-size:56px;flex:none;width:56px">✓</span>'
        f'<p style="margin:0;font-size:40px;line-height:1.25;font-weight:700">{e(t)}</p></div>' for t in s["items"])
    return (kicker(s["kicker"], accent, pill=True) + title(s.get("title1", "Mon lien est"), s.get("title2", "dans ma bio."), 160)
        + f'<div style="margin-top:48px;background:{CARD};border-radius:22px;padding:40px;display:flex;flex-direction:column;gap:28px">{items}</div>'
        + f'<p style="margin:32px 0 0;font-size:31px;line-height:1.35;color:{MUTED}">{e(s["disclaimer"])}</p>'
        + f'<div class="a" style="margin-top:36px;font-size:82px;line-height:1;text-align:center">ENREGISTRE. <span class="ac">TESTE.</span> MESURE.</div>'
        + '<p style="margin:12px 0 0;font-size:34px;font-weight:700;text-align:center">Abonne-toi pour d’autres pistes de revenus.</p>')

def main(path):
    c = json.load(open(path, encoding="utf-8"))
    out = os.path.dirname(os.path.abspath(path))
    accent = c.get("accent", "#F07A5F")
    handle = c.get("handle", "@classpro36")
    bodies = [slide1(c["slide1"], accent), slide2(c["slide2"], accent), slide3(c["slide3"], accent), slide4(c["slide4"], accent)]
    files = []
    for i, b in enumerate(bodies, 1):
        f = os.path.join(out, f"slide-{i}.html")
        open(f, "w", encoding="utf-8").write(page(b, accent, handle, i))
        files.append(f)
    r = subprocess.run(["node", os.path.join(ROOT, "tools", "shot.js"), *files], capture_output=True, text=True)
    print(r.stdout, r.stderr)
    for f in files:
        os.remove(f)
    if r.returncode != 0:
        sys.exit("ÉCHEC : texte qui déborde ou erreur de rendu, voir ci-dessus.")

if __name__ == "__main__":
    main(sys.argv[1])
