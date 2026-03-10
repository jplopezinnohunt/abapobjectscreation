const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    // We keep the cert policy just in case it handles the browser-level certificate prompt
    const autoSelectPolicy = JSON.stringify({
        pattern: 'https://hq-sap-d01.hq.int.unesco.org:443',
        filter: { SUBJECT: { CN: 'JP_LOPEZ' } }
    });

    const browser = await chromium.launch({
        headless: false,
        args: [`--auto-select-certificate-for-urls=${autoSelectPolicy}`]
    });

    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();

    const taskDir = path.resolve(__dirname);
    console.log('Task directory:', taskDir);

    console.log('Navigating to SAP GUI / ST22...');

    try {
        await page.goto('https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350&~transaction=ST22', {
            waitUntil: 'domcontentloaded',
            timeout: 60000
        });
    } catch (e) {
        console.log('Timeout during initial goto, but checking page state anyway...');
    }

    // Give the page some time to settle, wait for potential SSO redirect
    await page.waitForTimeout(5000);

    const pageTitle = await page.title();
    console.log('Current page title:', pageTitle);
    await page.screenshot({ path: path.join(taskDir, '01_sso_screen.png'), fullPage: true });

    // Handle the screen with 2 options
    // Looking for an element containing 'jp_lopez' (case insensitive)
    const jpLopezLocator = page.locator('text=/jp_lopez/i');

    if (await jpLopezLocator.count() > 0) {
        console.log(`Found ${await jpLopezLocator.count()} options matching jp_lopez, clicking the first one...`);
        await jpLopezLocator.first().click();

        // Wait a bit for the click to trigger navigation or popup
        await page.waitForTimeout(3000);

        // Wait for network to be idle after SSO selection
        try {
            await page.waitForLoadState('networkidle', { timeout: 15000 });
        } catch (e) {
            console.log('Timeout waiting for networkidle after SSO click, proceeding anyway.');
        }
    } else {
        console.log('SSO jp_lopez text not found, might already be authenticated or using a different term.');
    }

    console.log('Waiting for SAP GUI to fully load (10 seconds)...');
    await page.waitForTimeout(10000);
    await page.screenshot({ path: path.join(taskDir, '02_before_f8.png'), fullPage: true });

    console.log('Sending F8 Key Press to Execute ST22 today search...');
    await page.locator('body').focus();
    await page.keyboard.press('F8');

    console.log('Waiting 15 seconds for ST22 results to render...');
    await page.waitForTimeout(15000);

    console.log('Taking final screenshot...');
    const st22PngPath = path.join(taskDir, '03_st22_results.png');
    await page.screenshot({ path: st22PngPath, fullPage: true });

    let frames = page.frames();
    let content = "No WebGUI frame found, saving main page content instead.\n\n";
    let targetFrame = frames.find(f => f.url().includes('sap/bc/gui/sap/its/webgui') || f.url().includes('~transaction=ST22'));

    let textContent = "No WebGUI frame found, saving main page text instead.\n\n";

    if (targetFrame) {
        console.log('WebGUI frame found for HTML and Text dump.');
        content = await targetFrame.content();
        textContent = await targetFrame.evaluate(() => document.body.innerText);
    } else {
        content += await page.content();
        textContent = await page.evaluate(() => document.body.innerText);
    }

    fs.writeFileSync(path.join(taskDir, 'st22.html'), content);
    fs.writeFileSync(path.join(taskDir, 'st22_data.txt'), textContent);

    console.log('Script completed successfully. All outputs saved in:', taskDir);
    await browser.close();
})();
