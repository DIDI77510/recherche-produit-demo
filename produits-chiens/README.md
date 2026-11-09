# Carrousels TikTok — produits chiens (boutique revendix77)

- `photos/` : vraies photos des produits (envoyées par BIB le 9/11/2026). Réutiliser, ne jamais remplacer par des images générées.
- `posts/<AAAA-MM-JJ>-<HHMM>-<produit>/content.json` : textes du carrousel (4 à 6 slides : `hook`, `benefit`, `price`).
- `python3 produits-chiens/tools/build.py produits-chiens/posts/<dossier>/content.json` : génère `slide-N.jpg` (1080×1920, JPEG — TikTok refuse le PNG) et échoue si un texte déborde.
- URL publiques : `https://raw.githubusercontent.com/DIDI77510/recherche-produit-demo/main/produits-chiens/posts/<dossier>/slide-N.jpg`

Prérequis : Python 3 + Playwright (Chromium) + Pillow. Polices : `carrousels-tiktok/fonts/`.
