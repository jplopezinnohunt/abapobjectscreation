/**
 * se24_create_and_activate.js
 * 
 * Uses Playwright via CDP to:
 *   1. Open SE24, create ZCL_CRP_PROCESS_REQ class (if not exists)
 *   2. Activate ZCL_CRP_PROCESS_REQ
 *   3. Activate ZCL_Z_CRP_SRV_DPC_EXT
 * 
 * Connects to pre-authenticated Chrome on port 9222.
 * Run: node se24_create_and_activate.js
 */
const { chromium } = require('playwright');

const SAP_URL = 'https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350';
const TRANSPORT = 'D01K9B0EWT';

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getMainFrame(page) {
    await sleep(1500);
    const frames = page.frames();
    // Find the main content frame (not the top-level)
    for (const f of frames) {
        const url = f.url();
        if (url.includes('webgui') || url.includes('SAPWB')) return f;
    }
    return page.mainFrame();
}

async function enterTransaction(page, tcode) {
    console.log(`\n==> Navigating to ${tcode}...`);
    // Use the OK_CODE field (transaction input box)
    await page.goto(SAP_URL + `&sap-transaction=${tcode}`, { waitUntil: 'networkidle' });
    await sleep(2000);
}

async function openSE24Class(page, className) {
    console.log(`\n==> Opening SE24 for ${className}...`);
    await enterTransaction(page, 'SE24');
    await sleep(2000);

    const frame = await getMainFrame(page);

    // Enter class name in the object name field
    try {
        await frame.locator('[name="RS38M-PROGRAMM"], [id*="TYPNAME"], input[type="text"]').first().fill(className);
    } catch (e) {
        // Fallback: find the first text input
        await frame.locator('input[type="text"]').first().fill(className);
    }
    await sleep(500);
}

async function createClass(page, className) {
    console.log(`\n==> Creating class ${className}...`);
    await openSE24Class(page, className);
    const frame = await getMainFrame(page);

    // Click "Create" button (F5)
    try {
        await frame.locator('button[title*="Create"], [title="Create"], [accesskey="5"]').first().click();
    } catch (e) {
        await page.keyboard.press('F5');
    }
    await sleep(2000);

    // Fill the class description dialog
    try {
        const descInput = frame.locator('input[type="text"]').nth(1);
        await descInput.fill('CRP Process Request Business Logic Class');
        await sleep(300);
    } catch (e) {
        console.log('  Could not fill description:', e.message);
    }

    // Set Final/Public if dialog offers it
    try {
        await frame.locator('input[name*="FINAL"], input[value="Final"]').check();
    } catch (e) { /* optional */ }

    // Confirm creation (Enter or Save)
    await page.keyboard.press('Enter');
    await sleep(2000);

    // Set transport order if prompted
    await handleTransportDialog(page, frame);
    await sleep(1000);
    console.log(`  Class ${className} creation submitted.`);
}

async function activateClass(page, className) {
    console.log(`\n==> Activating ${className} in SE24...`);
    await openSE24Class(page, className);
    const frame = await getMainFrame(page);

    // Press Display (F7) first to load, then Activate (Ctrl+F3)
    try {
        await frame.locator('[title*="Display"], button[accesskey="7"]').first().click();
    } catch (e) {
        await page.keyboard.press('F7');
    }
    await sleep(2500);

    // Activate: Ctrl+F3 or the Activate toolbar button
    console.log('  Pressing Activate (Ctrl+F3)...');
    await page.keyboard.press('Control+F3');
    await sleep(3000);

    // Handle any "Inactive objects" popup — press Yes/Continue
    try {
        const frame2 = await getMainFrame(page);
        const yesBtn = frame2.locator('button:has-text("Yes"), button:has-text("Continue"), [title="Yes"]');
        const count = await yesBtn.count();
        if (count > 0) {
            await yesBtn.first().click();
            await sleep(2000);
        }
    } catch (e) { /* no popup */ }

    await handleTransportDialog(page, await getMainFrame(page));
    await sleep(1500);
    console.log(`  ${className} activation requested.`);
}

async function handleTransportDialog(page, frame) {
    try {
        await sleep(1000);
        const f = await getMainFrame(page);
        // Check if transport dialog appeared
        const trInput = f.locator('input[type="text"]').first();
        const val = await trInput.inputValue().catch(() => '');
        if (val === '' || val.length < 5) {
            // Fill transport order
            await trInput.fill(TRANSPORT);
            await sleep(300);
            await page.keyboard.press('Enter');
            await sleep(1000);
            console.log(`  Transport ${TRANSPORT} entered.`);
        }
    } catch (e) { /* no transport dialog */ }
}

async function main() {
    console.log('='.repeat(60));
    console.log('SE24 CLASS CREATION & ACTIVATION — SAP D01/350');
    console.log('='.repeat(60));

    let browser;
    try {
        browser = await chromium.connectOverCDP('http://localhost:9222');
        const contexts = browser.contexts();
        if (!contexts.length) throw new Error('No browser contexts found. Is Chrome running on port 9222?');

        const ctx = contexts[0];
        const pages = ctx.pages();
        let page = pages.find(p => p.url().includes('unesco')) || pages[0];

        if (!page) {
            page = await ctx.newPage();
        }

        console.log(`Using page: ${page.url()}`);

        // STEP 1: Create ZCL_CRP_PROCESS_REQ
        await createClass(page, 'ZCL_CRP_PROCESS_REQ');

        // STEP 2: Activate ZCL_CRP_PROCESS_REQ  
        await activateClass(page, 'ZCL_CRP_PROCESS_REQ');

        // STEP 3: Activate ZCL_Z_CRP_SRV_DPC_EXT
        await activateClass(page, 'ZCL_Z_CRP_SRV_DPC_EXT');

        console.log('\n' + '='.repeat(60));
        console.log('PLAYWRIGHT STEPS COMPLETE');
        console.log('Next: Verify activation status in SE24.');
        console.log('='.repeat(60));

    } catch (e) {
        console.error('\n[ERROR]', e.message);
        if (e.message.includes('9222') || e.message.includes('connect')) {
            console.error('=> Chrome is not running on port 9222.');
            console.error('=> Run: node 00_launch_browser.js');
        }
    } finally {
        if (browser) await browser.close().catch(() => { });
    }
}

main();
