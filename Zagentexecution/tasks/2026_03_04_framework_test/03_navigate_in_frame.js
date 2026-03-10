/**
 * 03_navigate_in_frame.js
 * Navigation within iframe context
 *
 * Learning #2: Command field is in FRAME, not main page
 * Solution: Search in frame context
 */

const { chromium } = require('playwright');

async function navigateInFrame() {
    console.log('========================================');
    console.log('Navigation IN FRAME');
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

        // Take screenshot of current state
        await page.screenshot({ path: '03_before_navigation.png', fullPage: true });
        console.log('✓ Before screenshot\n');

        // Search in FRAME for command field
        const commandFieldSelectors = [
            'input[name="~command"]',
            'input[id*="command"]',
            'input[id*="okcd"]',
            'input[title*="Command"]',
            'input[title*="OK"]',
            '#okcd'
        ];

        console.log('Searching for command field IN FRAME...');
        let commandField = null;

        for (const selector of commandFieldSelectors) {
            console.log(`  Trying: ${selector}`);
            try {
                const field = frame.locator(selector).first();
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
            console.log('\n⚠️ Still not found. Listing all inputs in frame...\n');

            const inputs = await frame.locator('input').evaluateAll(els =>
                els.map(el => ({
                    id: el.id,
                    name: el.name,
                    title: el.title,
                    type: el.type,
                    value: el.value,
                    visible: el.offsetParent !== null
                }))
            );

            console.log('All inputs in frame:');
            inputs.forEach((i, idx) => {
                if (i.visible) {
                    console.log(`  [${idx}] ID:"${i.id}" Name:"${i.name}" Title:"${i.title}" Type:${i.type}`);
                }
            });

            // Try first visible input as fallback
            console.log('\nTrying first visible input...');
            const firstInput = frame.locator('input').first();
            if (await firstInput.isVisible({ timeout: 1000 })) {
                commandField = firstInput;
                const id = await firstInput.getAttribute('id');
                console.log(`Using first input: ${id}\n`);
            } else {
                throw new Error('No input fields accessible');
            }
        }

        // Navigate to SEGW
        console.log('Typing /nSEGW...');
        await commandField.click();
        await commandField.fill('/nSEGW');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(4000);

        console.log('✓ Navigation sent, waiting...\n');

        // Take screenshot after navigation
        await page.screenshot({ path: '03_after_navigation.png', fullPage: true });
        console.log('✓ After navigation screenshot\n');

        // Check for popup
        await page.waitForTimeout(2000);
        const popup = frame.locator('.urPW').first();
        const hasPopup = await popup.isVisible({ timeout: 2000 }).catch(() => false);

        if (hasPopup) {
            console.log('✓ Popup detected');
            const titleElem = frame.locator('.urPWTitle').first();
            const title = await titleElem.innerText().catch(() => '');
            console.log('  Title:', title);

            console.log('  Filling: Z_CRP_SRV');
            const input = frame.locator('.urPW input[type="text"]').first();
            await input.fill('Z_CRP_SRV');
            await page.keyboard.press('Enter');
            await page.waitForTimeout(3000);
            console.log('✓ Project name entered\n');
        } else {
            console.log('ℹ No popup - checking current transaction...\n');
        }

        // Final state
        await page.screenshot({ path: '03_final_state.png', fullPage: true });
        console.log('✓ Final screenshot\n');

        console.log('========================================');
        console.log('✓✓✓ Navigation Complete ✓✓✓');
        console.log('========================================');

    } catch (error) {
        console.error('\n✗ Error:', error.message);
        console.error(error.stack);
        throw error;
    }
}

navigateInFrame().catch(console.error);
