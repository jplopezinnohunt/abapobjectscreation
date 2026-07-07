const G = require('./sap_gui_lib');
const AMT = '100000';
const PROJECTS = ['218BDI2000','501UZB5002','728RAS2003','547RAF1001','520RAF1015',
                  '503RAF1003','526RAS1036','927CMR5001','218BDI5000'];

async function statusText(page) {
    const f = await G.frame(page);
    return await f.evaluate(() => {
        const el = document.querySelector('#sbar-txt, .lsStatusbar__text, [id*="StatusBar"] span, .urStatusbar');
        if (el) return el.innerText.trim();
        const t = document.body.innerText.split('\n').map(s=>s.trim()).filter(Boolean);
        return t.find(s => /posted|active|error|does not|exceeded/i.test(s)) || '';
    }).catch(()=>'');
}

async function budgetEntry(page, tcode, proj) {
    await G.tcode(page, tcode);
    let f = await G.frame(page);
    await f.locator('input[title="Project definition"]').first().fill(proj);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(1200);
    f = await G.frame(page);
    const cell = f.locator('input[id*="[1,4]_c"]').first();
    await cell.click(); await cell.fill(AMT);
    await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(900);
    f = await G.frame(page);
    const save = f.locator('div[title^="Save"], [title="Save (Ctrl+S)"]').first();
    if (await save.count()) await save.click(); else await page.keyboard.press('Control+s');
    await G.idle(page); await page.waitForTimeout(1200);
    return await statusText(page);
}

async function cjbv(page, proj) {
    await G.tcode(page, 'CJBV');
    let f = await G.frame(page);
    await f.locator('input[title="Project definition"]').first().fill(proj);
    await page.keyboard.press('F8');
    await G.idle(page); await page.waitForTimeout(1500);
    return await statusText(page);
}

(async () => {
    const { page } = await G.connect();
    for (const p of PROJECTS) {
        const s30 = await budgetEntry(page, 'CJ30', p);
        const s32 = await budgetEntry(page, 'CJ32', p);
        const sbv = await cjbv(page, p);
        console.log(`${p}  CJ30[${s30}]  CJ32[${s32}]  CJBV[${sbv}]`);
    }
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
