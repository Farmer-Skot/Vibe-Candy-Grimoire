// Renders docs/<book>/print.html to docs/<book>/<book>.pdf with headless Chromium.
// Usage: node tools/make_pdf.js      (needs the `playwright` package)
const { chromium } = require('playwright');
const path = require('path');
const books = ['hermetic-codex', 'gnostic-grimoire'];
(async () => {
  const browser = await chromium.launch();
  for (const b of books) {
    const page = await browser.newPage();
    const dir = path.join(__dirname, '..', 'docs', b);
    await page.goto('file://' + path.join(dir, 'print.html'));
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({
      path: path.join(dir, b + '.pdf'),
      format: 'Letter',
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: true,
      headerTemplate: '<span></span>',
      footerTemplate: '<div style="width:100%;text-align:center;font-size:8px;color:#5d4a35;font-family:serif"><span class="pageNumber"></span></div>',
    });
    await page.close();
    console.log('wrote', b + '.pdf');
  }
  await browser.close();
})();
