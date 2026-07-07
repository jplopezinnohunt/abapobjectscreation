const G = require('./sap_gui_lib');
const PROJ = process.argv[2] || '549RAF2004';
(async () => {
    const { page } = await G.connect();
    let f = await G.frame(page);
    await f.locator('input[title="Project definition"]').first().fill(PROJ);
    await page.keyboard.press('F8');
    await G.idle(page); await page.waitForTimeout(2000);
    await G.dump(page, 'CJBV after execute ' + PROJ);
    await G.shot(page, 'cjbv_result');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
