const G = require('./sap_gui_lib');
const PROJ = process.argv[2] || '549RAF2004';
(async () => {
    const { page } = await G.connect();
    await G.tcode(page, 'CJ30');
    let f = await G.frame(page);
    await f.locator('input[title="Project definition"]').fill(PROJ);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1500);
    const info = await G.dump(page, 'CJ30 budget overview ' + PROJ);
    await G.shot(page, 'cj30_v01_overview');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
