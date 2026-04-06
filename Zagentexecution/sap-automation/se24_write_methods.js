/**
 * se24_write_methods.js
 * 
 * For each method in ZCL_Z_CRP_SRV_DPC_EXT:
 *   1. Opens the method in SE24 via CDP Playwright
 *   2. This triggers SAP to create the CM include for that method
 *   3. Script then saves with empty body (so include exists)
 * 
 * After this run, use write_to_cm_includes.py to write the real code via RFC.
 * 
 * Connect to Chrome started by: node launch_chrome_sap.js
 */
const { chromium } = require('playwright');

const SAP_BASE = 'https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350';
const TARGET_CLASS = 'ZCL_Z_CRP_SRV_DPC_EXT';

// Methods to initialize (open in SE24 so CM includes are created)
const DPC_METHODS = [
    'CRPCERTIFICATESET_GET_ENTITYSET',
    'CRPCERTIFICATESET_GET_ENTITY',
    'CRPCERTIFICATESET_CREATE_ENTITY',
    'CRPCERTIFICATESET_UPDATE_ENTITY',
    'CRPBUDGETLINESET_GET_ENTITYSET',
    'CRPBUDGETLINESET_CREATE_ENTITY',
    'CRPBUDGETLINESET_UPDATE_ENTITY',
    'CRPBUDGETLINESET_DELETE_ENTITY',
    'CRPAPPROVALHISTORYSET_GET_ENTITYSET',
    'CRPAPPROVALHISTORYSET_GET_ENTITY',
    'COSTRATESET_GET_ENTITYSET',
    'COSTRATESET_GET_ENTITY',
    'SUBMITFORAPPROVAL_FI',
    'SIMULATEJVPOSTING_FI',
    'POSTJV_FI',
    'POSTALLOTMENT_FI',
];

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getFrame(page) {
    await sleep(2000);
    const all = page.frames();
    // Find the main content frame (look for webgui content)
    for (const f of all) {
        if (f.url().includes('webgui') || f.url().includes('sap') || f.url().includes('bsp')) {
            if (f !== page.mainFrame()) return f;
        }
    }
    // Fallback to last non-main frame
    if (all.length > 1) return all[all.length - 1];
    return page.mainFrame();
}

async function main() {
    console.log('Connecting to Chrome on port 9222...');
    let browser;
    try {
        browser = await chromium.connectOverCDP('http://localhost:9222');
    } catch (e) {
        console.error('Cannot connect. Start Chrome first:\n  node launch_chrome_sap.js');
        return;
    }

    const ctx = browser.contexts()[0];
    const pages = ctx.pages();
    let page = pages.find(p => p.url().includes('sap')) || pages[0];
    if (!page) { page = await ctx.newPage(); }

    console.log(`Using page: ${page.url()}`);

    // Navigate to SE24
    const se24Url = `${SAP_BASE}&sap-transaction=SE24`;
    console.log('\nOpening SE24...');
    await page.goto(se24Url, { waitUntil: 'networkidle', timeout: 30000 });
    await sleep(3000);

    // Enter class name
    let frame = await getFrame(page);
    console.log(`\nEntering class: ${TARGET_CLASS}`);

    let classInput;
    try {
        // Try TYPNAME field (SE24 specific)
        classInput = frame.locator('[name*="TYPNAME"], [id*="TYPNAME"]').first();
        await classInput.waitFor({ timeout: 5000 });
    } catch (e) {
        // Fallback to first text input
        classInput = frame.locator('input[type="text"]').first();
    }

    await classInput.fill(TARGET_CLASS);
    await sleep(500);

    // Click Display (F7) to open class
    try {
        const displayBtn = frame.locator('[title="Display"], button:has-text("Display"), [accesskey="7"]').first();
        await displayBtn.click({ timeout: 3000 });
    } catch (e) {
        await page.keyboard.press('F7');
    }
    await sleep(3000);

    console.log('Class opened. Taking screenshot of current state...');
    await page.screenshot({ path: 'se24_state.png' });

    // Click Methods tab
    frame = await getFrame(page);
    console.log('Clicking Methods tab...');
    try {
        const methodsTab = frame.locator('text=Methods, [title="Methods"]').first();
        await methodsTab.click({ timeout: 5000 });
        await sleep(2000);
    } catch (e) {
        console.log('  Could not click Methods tab:', e.message);
    }

    await page.screenshot({ path: 'se24_methods_tab.png' });
    console.log('Screenshots saved: se24_state.png, se24_methods_tab.png');
    console.log('\nClass opened in SE24. Please check the browser state.');
    console.log('If authenticated, you can now see the Methods list.\n');

    // Report which methods we found
    frame = await getFrame(page);
    const rows = await frame.locator('tr').all();
    console.log(`Found ${rows.length} rows on page.`);

    await browser.close().catch(() => { });
}

main().catch(console.error);
