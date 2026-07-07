/**
 * CJ30 inspection — navigate to CJ30 for pilot WBS, dump the screen to build automation.
 * Connects to live D01 WebGUI session via CDP (Chrome on :9222).
 */
const SapConnection = require('../../../lib/sap-webgui-core/SapConnection');

const PROJECT = process.argv[2] || '549RAF2004';

(async () => {
    const conn = await SapConnection.connect('http://localhost:9222');
    await conn.navigateToTransaction('CJ30');
    await conn.page.waitForTimeout(1500);

    // Dump visible input fields + their labels/ids on the CJ30 initial screen
    const dump = async (tag) => {
        const info = await conn.frame.evaluate(() => {
            const out = { inputs: [], buttons: [], texts: [] };
            document.querySelectorAll('input[type=text], input:not([type])').forEach(i => {
                if (i.offsetParent !== null) out.inputs.push({ id: i.id, name: i.name, title: i.title, value: i.value });
            });
            document.querySelectorAll('[role=button], .lsButton, div[ct=B]').forEach(b => {
                const t = (b.title || b.innerText || '').trim();
                if (t && b.offsetParent !== null) out.buttons.push(t.slice(0, 30));
            });
            return out;
        });
        console.log(`\n===== ${tag} =====`);
        console.log('INPUTS:', JSON.stringify(info.inputs.slice(0, 25), null, 1));
        console.log('BUTTONS:', [...new Set(info.buttons)].slice(0, 30).join(' | '));
    };

    await dump('CJ30 initial screen');
    await conn.screenshot('cj30_initial');

    // Try to fill the project definition field and Enter
    const filled = await conn.frame.evaluate((proj) => {
        const cands = [...document.querySelectorAll('input[type=text], input:not([type])')]
            .filter(i => i.offsetParent !== null);
        // first visible editable input is usually the project def
        if (cands[0]) { cands[0].value = proj; cands[0].dispatchEvent(new Event('change', { bubbles: true })); return cands[0].id || cands[0].name; }
        return null;
    }, PROJECT);
    console.log('\nFilled project into field:', filled);
    await conn.page.keyboard.press('Enter');
    await conn.waitForIdle();
    await conn.page.waitForTimeout(2000);

    await dump('CJ30 after project entered');
    await conn.screenshot('cj30_budget_screen');
    console.log('\nStatus bar:', await conn.getStatusBarMessage());

    // don't close — leave session for next steps
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
