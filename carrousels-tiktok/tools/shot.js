// Rend chaque slide-N.html en slide-N.png et vérifie qu'aucun texte ne déborde.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1440 } });
  let bad = 0;
  for (const f of process.argv.slice(2)) {
    await p.goto('file://' + f, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    const m = await p.evaluate(() => {
      const c = document.getElementById('content').getBoundingClientRect();
      const ft = document.getElementById('foot').getBoundingClientRect();
      return { contentBottom: c.bottom, footTop: ft.top, footBottom: ft.bottom };
    });
    const ok = m.contentBottom <= m.footTop + 1 && m.footBottom <= 1440;
    console.log((ok ? 'OK   ' : 'TROP LONG ') + f.split('/').pop(), JSON.stringify(m));
    if (!ok) bad++;
    await p.screenshot({ path: f.replace(/\.html$/, '.png'), clip: { x: 0, y: 0, width: 1080, height: 1440 } });
  }
  await b.close();
  process.exit(bad ? 1 : 0);
})();
