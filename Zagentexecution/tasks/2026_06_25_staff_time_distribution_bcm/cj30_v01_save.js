const G = require('./sap_gui_lib');
(async () => {
    const { page } = await G.connect();
    let f = await G.frame(page);
    // click Save (toolbar). Fallback to Ctrl+S.
    const save = f.locator('div[title^="Save"], [title="Save (Ctrl+S)"]').first();
    if (await save.count()) { await save.click(); }
    else { await page.keyboard.press('Control+s'); }
    await G.idle(page); await page.waitForTimeout(1500);
    await G.dump(page, 'CJ30 after SAVE');
    await G.shot(page, 'cj30_v01_saved');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
