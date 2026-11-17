"""Carrousels (1080x1350 JPG) + petites vidéos (1080x1920 MP4) pour les produits Marie Virgile."""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

G = "/usr/share/fonts/truetype/google-fonts/"
SER = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
PG = os.environ.get("PAGES_DIR", "/home/claude/promo/pages/")
THEMES = {"vb": dict(bg=(244, 236, 226), ink=(58, 51, 64), acc=(201, 164, 106), soft=(231, 184, 168)),
          "ep": dict(bg=(243, 241, 234), ink=(47, 59, 58), acc=(201, 164, 106), soft=(143, 169, 138)),
          "val": dict(bg=(253, 243, 241), ink=(74, 42, 54), acc=(200, 66, 90), soft=(242, 184, 194)),
          "lun": dict(bg=(251, 243, 228), ink=(110, 16, 30), acc=(200, 16, 46), soft=(212, 162, 76)),
          "hab": dict(bg=(244, 238, 228), ink=(47, 59, 58), acc=(201, 120, 91), soft=(220, 231, 222)),
          "col": dict(bg=(246, 241, 232), ink=(45, 45, 52), acc=(201, 164, 106), soft=(220, 233, 226)),
          "tch": dict(bg=(251, 246, 238), ink=(51, 64, 74), acc=(62, 142, 138), soft=(251, 227, 220))}


def fr_nbsp(t):
    t = re.sub(r" (?=[?!:€»;])", "\u00a0", t)
    t = re.sub(r"(?<=«) ", "\u00a0", t)
    return re.sub(r"(?<=\d) (?=\d{3})", "\u00a0", t)


def wrap(d, text, font, maxw):
    out = []
    for para in fr_nbsp(text).split("\n"):
        cur = ""
        for w in [x for x in para.split(" ") if x]:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                cur = t
            else:
                out.append(cur); cur = w
        out.append(cur)
    return out


def text_block(d, y, text, font, fill, W, maxw, gap=1.18, align="c", x0=None):
    lines = wrap(d, text, font, maxw)
    lh = int(font.size * gap)
    for ln in lines:
        w = d.textlength(ln, font=font)
        x = (W - w) / 2 if align == "c" else x0
        d.text((x, y), ln, font=font, fill=fill); y += lh
    return y


def paste_page(c, name, h, center_x, top, angle=0):
    h = int(h); top = int(top)
    im = Image.open(PG + name).convert("RGB")
    w = int(im.width * h / im.height)
    if w > int(c.width * 0.8):
        w = int(c.width * 0.8); h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    if angle:
        im = im.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (im.width + 80, im.height + 80), (0, 0, 0, 0))
    mask = im.split()[-1] if im.mode == "RGBA" else Image.new("L", im.size, 255)
    sh.paste((40, 30, 20, 95), (40, 52), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    x = int(center_x - im.width / 2)
    c.paste(sh, (x - 40, top - 40), sh)
    if im.mode == "RGBA":
        c.paste(im, (x, top), im)
    else:
        c.paste(im, (x, top))
    return top + im.height


def render(slide, theme, W, H, idx, total, handle):
    T = THEMES[theme]; c = Image.new("RGB", (W, H), T["bg"]).convert("RGBA"); d = ImageDraw.Draw(c)
    s = W / 1080; M = int(70 * s); tall = H / W > 1.5
    ytop = int((150 if tall else 80) * s)
    k = slide["kind"]
    if k == "hook":
        y = ytop
        if slide.get("kicker"):
            f = F(G + "Poppins-Bold.ttf", int(34 * s)); t = slide["kicker"].upper(); w = d.textlength(t, font=f)
            d.rounded_rectangle([(W - w) / 2 - 28 * s, y, (W + w) / 2 + 28 * s, y + 62 * s], radius=31 * s, fill=T["acc"])
            d.text(((W - w) / 2, y + 9 * s), t, font=f, fill=(255, 255, 255)); y += int(100 * s)
        y = text_block(d, y, slide["big"], F(SER, int(slide.get("size", 84) * s)), T["ink"], W, W - 2 * M, 1.12)
        if slide.get("sub"):
            y = text_block(d, y + int(24 * s), slide["sub"], F(G + "Poppins-Regular.ttf", int(40 * s)), T["ink"], W, W - 2 * M - 40 * s)
        if slide.get("img"):
            hh = H - y - int((220 if tall else 110) * s)
            paste_page(c, slide["img"], max(int(300 * s), hh), W // 2, y + int(50 * s), slide.get("angle", -4))
    elif k == "page":
        y = text_block(d, ytop, slide["title"], F(SER, int(66 * s)), T["ink"], W, W - 2 * M)
        if slide.get("text"):
            y = text_block(d, y + int(10 * s), slide["text"], F(G + "Poppins-Regular.ttf", int(36 * s)), T["ink"], W, W - 2 * M)
        hh = H - y - int((230 if tall else 120) * s)
        paste_page(c, slide["img"], hh, W // 2, y + int(40 * s))
    elif k == "list":
        y = text_block(d, ytop, slide["title"], F(SER, int(66 * s)), T["ink"], W, W - 2 * M) + int(40 * s)
        f = F(G + "Poppins-Medium.ttf", int(40 * s))
        for i, it in enumerate(slide["items"]):
            r = int(30 * s)
            d.ellipse([M, y + 4 * s, M + 2 * r, y + 4 * s + 2 * r], fill=T["acc"])
            fn = F(G + "Poppins-Bold.ttf", int(30 * s)); n = str(i + 1); wn = d.textlength(n, font=fn)
            d.text((M + r - wn / 2, y + 10 * s), n, font=fn, fill=(255, 255, 255))
            y = text_block(d, y + 2 * s, it, f, T["ink"], W, W - 2 * M - 2 * r - 30 * s, 1.2, "l", M + 2 * r + 30 * s) + int(30 * s)
        if slide.get("img"):
            hh = H - y - int((220 if tall else 110) * s)
            if hh > 280 * s:
                paste_page(c, slide["img"], hh, W // 2, y + int(20 * s), slide.get("angle", 3))
    elif k == "cta":
        y = text_block(d, ytop, slide["title"], F(SER, int(70 * s)), T["ink"], W, W - 2 * M)
        hh = int((H - y) * (0.55 if tall else 0.5))
        y = paste_page(c, slide["img"], hh, W // 2, y + int(40 * s), -3) + int(60 * s)
        f = F(SER, int(96 * s)); t = slide["price"]; w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=T["acc"]); y += int(120 * s)
        f = F(G + "Poppins-Bold.ttf", int(40 * s)); t = slide["btn"]; w = d.textlength(t, font=f)
        d.rounded_rectangle([(W - w) / 2 - 40 * s, y, (W + w) / 2 + 40 * s, y + 80 * s], radius=40 * s, fill=T["ink"])
        d.text(((W - w) / 2, y + 14 * s), t, font=f, fill=(255, 255, 255)); y += int(110 * s)
        text_block(d, y, slide.get("small", ""), F(G + "Poppins-Regular.ttf", int(30 * s)), T["ink"], W, W - 2 * M)
    # pied : marque + pagination
    f = F(G + "Poppins-Medium.ttf", int(26 * s)); yb = H - int((150 if tall else 60) * s)
    d.text((M, yb), "Marie Virgile", font=f, fill=T["ink"])
    t = handle; w = d.textlength(t, font=f); d.text(((W - w) / 2, yb), t, font=f, fill=T["ink"])
    if total > 1:
        t = f"{idx}/{total}"; w = d.textlength(t, font=f); d.text((W - M - w, yb), t, font=f, fill=T["ink"])
    return c.convert("RGB")


def build(spec_path):
    spec = json.load(open(spec_path)); base = os.path.dirname(spec_path)
    n = len(spec["slides"]); car, vid = [], []
    for i, sl in enumerate(spec["slides"], 1):
        im = render(sl, spec["theme"], 1080, 1350, i, n, spec.get("handle", "@revendix77"))
        p = os.path.join(base, f"slide-{i}.jpg"); im.save(p, quality=90); car.append(p)
        if spec.get("video"):
            im = render(sl, spec["theme"], 1080, 1920, i, 0, spec.get("handle", "@revendix77"))
            p = os.path.join(base, f"v-{i}.jpg"); im.save(p, quality=92); vid.append(p)
    if vid:
        dur, fade = 3.0, 0.5
        inputs, filt = [], []
        for i, p in enumerate(vid):
            inputs += ["-loop", "1", "-t", str(dur), "-i", p]
            filt.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(zoom+0.0009,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*30)}:s=1080x1920:fps=30,setsar=1,format=yuv420p[s{i}]")
        last = "s0"; off = dur - fade
        for i in range(1, len(vid)):
            filt.append(f"[{last}][s{i}]xfade=transition=fade:duration={fade}:offset={off:.2f}[x{i}]"); last = f"x{i}"; off += dur - fade
        out = os.path.join(base, "video.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-f", "lavfi", "-t", f"{off+fade:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
               "-filter_complex", ";".join(filt), "-map", f"[{last}]", "-map", f"{len(vid)}:a", "-c:v", "libx264", "-preset", "medium",
               "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out]
        subprocess.run(cmd, check=True)
        for p in vid: os.remove(p)
        im = render(spec["slides"][0], spec["theme"], 1080, 1920, 1, 0, spec.get("handle", "@revendix77")); im.save(os.path.join(base, "cover.jpg"), quality=90)
    print(base, len(car), "slides", "+ video" if vid else "")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
