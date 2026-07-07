const G = require('./sap_gui_lib');
const AMT = process.argv[2] || '100000';
(async () => {
    const { page } = await G.connect();
    let f = await G.frame(page);
    // budget cell of the top WBS row (col "Budget" = index 4, first data row)
    const cell = f.locator('[id="tbl47[1,4]_c"]');
    await cell.click();
    await cell.fill(AMT);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1200);
    await G.dump(page, 'CJ30 after entering budget ' + AMT);
    await G.shot(page, 'cj30_v01_entered');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
