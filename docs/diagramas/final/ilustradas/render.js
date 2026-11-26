// Converte um SVG desta pasta (ou de ..) em PNG. Uso: node render.js entrada.svg saida.png [escala=2]
// Precisa do Playwright com Chromium e da fonte Inter instalada (sem ela cai para DejaVu Sans).
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [ent, sai, esc] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ deviceScaleFactor: Number(esc || 2) });
  await p.goto('file://' + path.resolve(ent));
  const s = await p.evaluate(() => { const e = document.querySelector('svg'); return { w: e.width.baseVal.value, h: e.height.baseVal.value }; });
  await p.setViewportSize({ width: Math.ceil(s.w), height: Math.ceil(s.h) });
  await p.screenshot({ path: sai, clip: { x: 0, y: 0, width: Math.ceil(s.w), height: Math.ceil(s.h) } });
  await b.close();
})();
