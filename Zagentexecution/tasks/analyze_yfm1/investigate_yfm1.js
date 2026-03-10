const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { SapConnection, SapMenu, SapSession } = require('../../../lib/sap-webgui-core');

(async () => {
    const taskDir = path.resolve(__dirname);
    console.log('Task directory:', taskDir);

    const autoSelectPolicy = JSON.stringify({
        pattern: 'https://hq-sap-d01.hq.int.unesco.org:443',
        filter: { SUBJECT: { CN: 'JP_LOPEZ' } }
    });

    console.log('Launching browser...');
    const browser = await chromium.launch({
        headless: false,
        args: [`--auto-select-certificate-for-urls=${autoSelectPolicy}`]
    });

    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();

    console.log('Navigating to SAP WebGUI...');
    try {
        await page.goto('https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350', {
            waitUntil: 'domcontentloaded',
            timeout: 60000
        });
    } catch (e) {
        console.log('Initial goto timeout, checking state...');
    }

    await page.waitForTimeout(5000);

    // Handle SSO if needed
    const jpLopezLocator = page.locator('text=/jp_lopez/i');
    if (await jpLopezLocator.count() > 0) {
        console.log('Found SSO option, clicking...');
        await jpLopezLocator.first().click();
        await page.waitForTimeout(5000);
    }

    // Wait for the main SAP frame
    console.log('Waiting for SAP frame...');
    let frames = page.frames();
    let sapFrame = frames.find(f => f.name().startsWith('itsframe1_'));

    let retry = 0;
    while (!sapFrame && retry < 10) {
        await page.waitForTimeout(2000);
        frames = page.frames();
        sapFrame = frames.find(f => f.name().startsWith('itsframe1_'));
        retry++;
    }

    if (!sapFrame) {
        console.error('SAP frame NOT found. Taking error screenshot.');
        await page.screenshot({ path: path.join(taskDir, 'error_no_frame.png'), fullPage: true });
        await browser.close();
        process.exit(1);
    }

    console.log('SAP Frame found:', sapFrame.name());

    // Create connection object for generic framework use
    const conn = new SapConnection(browser, page, sapFrame);
    const menu = new SapMenu(sapFrame, page);
    const session = new SapSession(sapFrame, page);

    console.log('Navigating to YFM1...');
    await conn.navigateToTransaction('YFM1');
    await page.waitForTimeout(5000);
    await page.screenshot({ path: path.join(taskDir, '01_yfm1_main.png'), fullPage: true });

    console.log('Getting System -> Status...');
    // SAP WebGUI often wraps menus in a "More" button or different IDs
    // Let's try to click the System menu directly using a text filter if IDs fail
    try {
        const systemMenu = sapFrame.locator('span, div, a').filter({ hasText: /^System$/ }).first();
        if (await systemMenu.isVisible()) {
            await systemMenu.click();
            await page.waitForTimeout(1000);
            const statusItem = sapFrame.locator('span, div, a').filter({ hasText: /^Status\.\.\.$/ }).first();
            if (await statusItem.isVisible()) {
                await statusItem.click();
            } else {
                console.log('Status item not found, trying keyboard navigation...');
                await page.keyboard.press('ArrowDown');
                await page.keyboard.press('Enter');
            }
        } else {
            console.log('System menu not found by text, trying alternative method...');
            // Try to use keyboard Shift+F10 for context menu or similar
        }
    } catch (e) {
        console.log('Menu interaction failed:', e.message);
    }
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(taskDir, '02_yfm1_status_dialog.png'), fullPage: true });

    // Extract text from the status dialog if possible
    const statusContent = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync(path.join(taskDir, 'yfm1_status_dump.txt'), statusContent);

    console.log('Investigation complete.');
    await browser.close();
})();
