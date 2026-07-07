// Generic PS budget entry (CJ30 original / CJ32 release) on the top WBS, one year.
const G = require('./sap_gui_lib');
const TCODE = process.argv[2];         // CJ30 | CJ32
const PROJ  = process.argv[3] || '549RAF2004';
const AMT   = process.argv[4] || '100000';
(async () => {
    const { page } = await G.connect();
    await G.tcode(page, TCODE);
    let f = await G.frame(page);
    await f.locator('input[title="Project definition"]').fill(PROJ);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1500);
    // editable cell: first data row, budget/release column (col index 4)
    f = await G.frame(page);
    const cell = f.locator('input[id*="[1,4]_c"]').first();
    await cell.click(); await cell.fill(AMT);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1000);
    // Save
    const save = f2 => f2.locator('div[title^="Save"], [title="Save (Ctrl+S)"]').first();
    let ff = await G.frame(page);
    if (await save(ff).count()) await save(ff).click(); else await page.keyboard.press('Control+s');
    await G.idle(page); await page.waitForTimeout(1500);
    await G.dump(page, `${TCODE} ${PROJ} after SAVE`);
    await G.shot(page, `${TCODE}_${PROJ}_saved`);
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
