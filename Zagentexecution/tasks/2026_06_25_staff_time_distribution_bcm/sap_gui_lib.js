/**
 * Minimal robust SAP WebGUI driver for the staff-time budget task.
 * Key fix vs core framework: RE-ACQUIRE the ITS iframe after every round-trip
 * (SAP recreates itsframe1_* on each server hit → stale refs are the #1 failure).
 */
const { chromium } = require('playwright');

async function connect(cdp = 'http://localhost:9222') {
    const browser = await chromium.connectOverCDP(cdp);
    const ctx = browser.contexts()[0];
    const page = ctx.pages().find(p => p.url().includes('webgui')) || ctx.pages()[0];
    return { browser, page };
}

// current live ITS frame
async function frame(page, timeout = 10000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        const f = page.frames().find(fr => fr.name().startsWith('itsframe1_'));
        if (f) { try { await f.evaluate(() => document.readyState); return f; } catch (e) { /* stale, retry */ } }
        await page.waitForTimeout(250);
    }
    return page.mainFrame();
}

async function idle(page) {
    const f = await frame(page);
    await f.waitForSelector('.urBusyIndicator', { state: 'hidden', timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(600);
}

// type a tcode via the command field (#ToolbarOkCode) and Enter
async function tcode(page, code) {
    const f = await frame(page);
    const cmd = f.locator('#ToolbarOkCode');
    await cmd.click(); await cmd.fill(`/n${code}`);
    await page.keyboard.press('Enter');
    await idle(page); await page.waitForTimeout(1000);
}

// dump visible inputs (with titles) + status bar of the CURRENT screen
async function dump(page, tag) {
    const f = await frame(page);
    const info = await f.evaluate(() => {
        const vis = el => el.offsetParent !== null;
        const inputs = [...document.querySelectorAll('input')].filter(vis)
            .map(i => ({ id: i.id, title: (i.title || '').slice(0, 40), value: i.value }));
        const sb = document.querySelector('.urStatusbar, #stbar-msg-txt');
        return { inputs: inputs.slice(0, 40), status: sb ? sb.innerText.trim() : null };
    });
    console.log(`\n===== ${tag} =====`);
    info.inputs.forEach(i => console.log(`  [${i.id}] "${i.title}" = "${i.value}"`));
    console.log('  STATUS:', info.status);
    return info;
}

async function shot(page, name) {
    const p = `Zagentexecution/tasks/2026_06_25_staff_time_distribution_bcm/shot_${name}.png`;
    await page.screenshot({ path: p });
    console.log('  shot:', p);
}

module.exports = { connect, frame, idle, tcode, dump, shot };
