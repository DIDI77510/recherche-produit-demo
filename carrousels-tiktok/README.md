# Carrousels TikTok — parrainages

Carrousels de 4 slides (1080×1440) publiés sur TikTok @classpro36 via Metricool.

- `posts/<date>-<marque>/content.json` : textes d'un carrousel, légende (`caption`) et titre TikTok (`title`).
- `python3 tools/build.py posts/<dossier>/content.json` : génère `slide-1.png` … `slide-4.png` et échoue si un texte déborde.
- Les images sont servies publiquement par `https://raw.githubusercontent.com/DIDI77510/recherche-produit-demo/main/carrousels-tiktok/posts/<dossier>/slide-N.png`.

Prérequis de rendu : Node + Playwright (Chromium), Python 3 avec Pillow.
