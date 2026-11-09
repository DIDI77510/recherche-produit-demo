#!/usr/bin/env python3
"""Génère les slides JPEG (1080x1920) d'un carrousel produit à partir d'un content.json.

Usage : python3 produits-chiens/tools/build.py produits-chiens/posts/<dossier>/content.json
Écrit slide-1.jpg ... slide-N.jpg à côté du JSON (JPEG uniquement : TikTok refuse le PNG).
Échoue si un texte déborde de sa zone.
"""
import json, os, sys, html
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FONTS = os.path.join(os.path.dirname(BASE), "carrousels-tiktok", "fonts")
PHOTOS = os.path.join(BASE, "photos")
BG, FG, MUTED = "#0B0B0B", "#FAF6F0", "#D9D2C8"


def e(s):
    return html.escape(str(s), quote=False)


def head(accent):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@font-face{{font-family:'Anton';src:url('file://{FONTS}/anton-latin-400-normal.woff2')}}
@font-face{{font-family:'DM Sans';font-weight:400;src:url('file://{FONTS}/dm-sans-latin-400-normal.woff2')}}
@font-face{{font-family:'DM Sans';font-weight:700;src:url('file://{FONTS}/dm-sans-latin-700-normal.woff2')}}
body{{margin:0;background:{BG}}}
.a{{font-family:'Anton',sans-serif;text-transform:uppercase}} .ac{{color:{accent}}}
#root{{width:1080px;height:1920px;position:relative;overflow:hidden;background:{BG};color:{FG};font-family:'DM Sans',sans-serif}}
.fit{{overflow:hidden}}
</style></head><body><div id="root">"""


def photo(p):
    return "file://" + os.path.join(PHOTOS, p)


def foot(handle, n, total):
    return (f'<div style="position:absolute;left:72px;right:72px;top:1500px;display:flex;justify-content:space-between;'
            f'font-size:30px;color:#BDB6AC;border-top:2px solid #333;padding-top:18px"><span>{e(handle)}</span><span>{n} / {total}</span></div>')


def hook(s, c, n, total):
    lines = "".join(f'<div>{e(l)}</div>' for l in s["lines"])
    acc = f'<div class="ac">{e(s["accent_line"])}</div>' if s.get("accent_line") else ""
    return (f'<img src="{photo(s["photo"])}" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;object-position:{s.get("pos","center")}">'
            '<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.88) 0%,rgba(0,0,0,.55) 38%,rgba(0,0,0,.15) 60%,rgba(0,0,0,.7) 100%)"></div>'
            f'<div class="fit" data-max="760" style="position:absolute;left:72px;right:150px;top:150px">'
            f'<div class="a ac" style="font-size:40px;letter-spacing:4px">{e(s["kicker"])}</div>'
            f'<div class="a" style="margin-top:24px;font-size:{s.get("size",150)}px;line-height:1.12">{lines}{acc}</div>'
            f'<p style="margin:30px 0 0;font-size:44px;line-height:1.25;font-weight:700">{e(s["sub"])}</p></div>'
            f'<div class="a" style="position:absolute;left:72px;top:1420px;font-size:44px;letter-spacing:2px">FAIS DÉFILER →</div>'
            + foot(c["handle"], n, total))


def benefit(s, c, n, total):
    fit = s.get("fit", "contain")
    bg = "#FFFFFF" if fit == "contain" else "#111"
    return (f'<div class="fit" data-max="560" style="position:absolute;left:72px;right:150px;top:130px">'
            f'<div class="a ac" style="font-size:40px;letter-spacing:4px">{e(s["kicker"])}</div>'
            f'<div class="a" style="margin-top:20px;font-size:{s.get("size",110)}px;line-height:1.2">{e(s["title"])}</div>'
            f'<p style="margin:24px 0 0;font-size:40px;line-height:1.3;color:{MUTED}">{e(s["text"])}</p></div>'
            f'<div style="position:absolute;left:72px;right:72px;top:720px;height:740px;border-radius:32px;overflow:hidden;background:{bg}">'
            f'<img src="{photo(s["photo"])}" style="width:100%;height:100%;object-fit:{fit};object-position:{s.get("pos","center")}"></div>'
            + foot(c["handle"], n, total))


def price(s, c, n, total):
    return (f'<div style="position:absolute;left:72px;right:72px;top:130px;height:660px;border-radius:32px;overflow:hidden;background:#fff">'
            f'<img src="{photo(s["photo"])}" style="width:100%;height:100%;object-fit:contain"></div>'
            f'<div class="fit" data-max="680" style="position:absolute;left:72px;right:150px;top:830px">'
            f'<div class="a" style="font-size:60px;line-height:1.05">{e(s["name"])}</div>'
            f'<p style="margin:10px 0 0;font-size:36px;color:{MUTED}">{e(s["detail"])}</p>'
            f'<div class="a ac" style="margin-top:14px;font-size:210px;line-height:1">{e(s["price"])}</div>'
            f'<div style="margin-top:22px;background:{c["accent"]};color:{BG};border-radius:20px;padding:24px 30px;font-size:42px;line-height:1.25;font-weight:700">'
            f'{e(s["cta"])}</div></div>'
            + foot(c["handle"], n, total))


KINDS = {"hook": hook, "benefit": benefit, "price": price}


def main(path):
    c = json.load(open(path))
    out = os.path.dirname(os.path.abspath(path))
    total = len(c["slides"])
    assert 4 <= total <= 6, "4 à 6 slides"
    bad = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for i, s in enumerate(c["slides"], 1):
            for p in [s.get("photo")]:
                assert p and os.path.exists(os.path.join(PHOTOS, p)), f"photo manquante : {p}"
            doc = head(c["accent"]) + KINDS[s["type"]](s, c, i, total) + "</div></body></html>"
            f = os.path.join(out, f"slide-{i}.html")
            open(f, "w").write(doc)
            pg.goto("file://" + f, wait_until="load")
            pg.evaluate("document.fonts.ready")
            over = pg.evaluate("""() => [...document.querySelectorAll('.fit')].filter(el => el.scrollHeight > +el.dataset.max).map(el => el.scrollHeight)""")
            if over:
                print(f"TROP LONG slide-{i}", over); bad += 1
            png = pg.screenshot(clip={"x": 0, "y": 0, "width": 1080, "height": 1920})
            Image.open(BytesIO(png)).convert("RGB").save(os.path.join(out, f"slide-{i}.jpg"), "JPEG", quality=90, optimize=True)
            os.remove(f)
            print("OK", f"slide-{i}.jpg")
        b.close()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1])
