const G = require('./sap_gui_lib');
const PROJ = process.argv[2] || '549RAF2004';
(async () => {
    const { page } = await G.connect();
    let f = await G.frame(page);
    // fill Project definition by title
    await f.locator('input[title="Project definition"]').fill(PROJ);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1200);
    await G.dump(page, 'CJ30 budget screen for ' + PROJ);
    await G.shot(page, 'cj30_budget');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
