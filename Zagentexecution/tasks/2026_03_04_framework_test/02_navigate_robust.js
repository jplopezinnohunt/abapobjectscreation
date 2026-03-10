/**
 * 02_navigate_robust.js
 * More robust navigation - try multiple strategies
 *
 * Learning #1: Command field selectors may vary
 * Solution: Try multiple selectors and visual inspection
 */

const { chromium } = require('playwright');

async function navigateRobust() {
    console.log('========================================');
    console.log('Robust Navigation to SEGW');
    console.log('========================================\n');

    try {
        // Connect
        const browser = await chromium.connectOverCDP('http://localhost:9222');
        const context = browser.contexts()[0];
        const page = context.pages().find(p => p.url().includes('webgui')) || context.pages()[0];

        console.log('Connected to:', page.url());

        // Find frame
        const frame = page.frames().find(f => f.name().startsWith('itsframe1_'));
        if (!frame) {
            throw new Error('Frame not found');
        }

        console.log('Frame found:', frame.name(), '\n');

        // Strategy 1: Look for command field by multiple selectors
        const commandFieldSelectors = [
            'input[id*="command"]',
            'input[name*="command"]',
            'input[title*="Command"]',
            'input[title*="OK-Code"]',
            '#okcd'  // Classic SAP command field ID
        ];

        console.log('Searching for command field...');
        let commandField = null;

        for (const selector of commandFieldSelectors) {
            console.log(`  Trying: ${selector}`);
            try {
                const field = page.locator(selector).first();
                if (await field.isVisible({ timeout: 1000 })) {
                    commandField = field;
                    console.log(`  ✓ Found with: ${selector}\n`);
                    break;
                }
            } catch (e) {
                console.log(`  ✗ Not found`);
            }
        }

        if (!commandField) {
            console.log('\n⚠️ Command field not found with standard selectors');
            console.log('Taking screenshot for manual inspection...');
            await page.screenshot({ path: '02_command_field_search.png', fullPage: true });

            // Try to list all input fields for debugging
            const inputs = await page.locator('input').evaluateAll(els =>
                els.map(el => ({
                    id: el.id,
                    name: el.name,
                    title: el.title,
                    type: el.type,
                    visible: el.offsetParent !== null
                }))
            );

            console.log('\nAll visible input fields:');
            inputs.filter(i => i.visible).forEach(i => {
                console.log(`  - ID: ${i.id}, Name: ${i.name}, Title: ${i.title}, Type: ${i.type}`);
            });

            throw new Error('Command field not accessible');
        }

        // Navigate to SEGW
        console.log('Typing /nSEGW...');
        await commandField.click();
        await commandField.fill('/nSEGW');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(3000);

        console.log('✓ Navigation sent\n');

        // Check for Open Project popup
        await page.waitForTimeout(2000);
        const popup = frame.locator('.urPW').first();
        const hasPopup = await popup.isVisible({ timeout: 2000 }).catch(() => false);

        if (hasPopup) {
            const titleElem = frame.locator('.urPWTitle').first();
            let title = '';
            if (await titleElem.isVisible({ timeout: 1000 })) {
                title = await titleElem.innerText();
                console.log('Popup detected:', title);
            }

            if (title.includes('Open') || title.includes('Project')) {
                console.log('Filling project name: Z_CRP_SRV');
                const input = frame.locator('.urPW input[type="text"]').first();
                await input.fill('Z_CRP_SRV');
                await page.keyboard.press('Enter');
                await page.waitForTimeout(3000);
                console.log('✓ Project opened\n');
            }
        }

        // Take final screenshot
        await page.screenshot({ path: '02_segw_loaded.png', fullPage: true });
        console.log('✓ Screenshot taken\n');

        console.log('========================================');
        console.log('✓✓✓ SUCCESS ✓✓✓');
        console.log('========================================');
        console.log('\nSEGW should now be loaded with Z_CRP_SRV');

    } catch (error) {
        console.error('\n✗ Error:', error.message);
        throw error;
    }
}

navigateRobust().catch(console.error);
