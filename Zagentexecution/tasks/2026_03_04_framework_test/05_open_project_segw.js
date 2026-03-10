/**
 * 05_open_project_segw.js
 * Force proper project opening in SEGW
 *
 * Learning #4: Toolbar C109 not visible = not in correct SEGW screen
 * Solution: Explicitly open project via UI
 */

const { chromium } = require('playwright');

async function openProjectSegw() {
    console.log('========================================');
    console.log('Force Open Project in SEGW');
    console.log('========================================\n');

    try {
        const browser = await chromium.connectOverCDP('http://localhost:9222');
        const context = browser.contexts()[0];
        const page = context.pages().find(p => p.url().includes('webgui')) || context.pages()[0];
        const frame = page.frames().find(f => f.name().startsWith('itsframe1_'));

        console.log('Connected\n');

        // Strategy 1: Look for "Open Project" button/icon
        console.log('Looking for Open Project button...');

        const openButtonSelectors = [
            '[title*="Open"]',
            '[title*="Project"]',
            'img[title*="Open"]',
            '[id*="btn"][title*="Open"]'
        ];

        let opened = false;

        for (const selector of openButtonSelectors) {
            try {
                const btn = frame.locator(selector).first();
                if (await btn.isVisible({ timeout: 1000 })) {
                    const title = await btn.getAttribute('title');
                    console.log(`  Found button: "${title}"`);

                    if (title && (title.includes('Open') || title.includes('Project'))) {
                        console.log('  Clicking...');
                        await btn.click({ force: true });
                        await page.waitForTimeout(2000);
                        opened = true;
                        break;
                    }
                }
            } catch (e) {}
        }

        if (!opened) {
            console.log('  ✗ Open button not found');
            console.log('\nTrying keyboard shortcut...');

            // Try Ctrl+O or F3
            await page.keyboard.press('Control+o');
            await page.waitForTimeout(1500);
        }

        // Check for popup
        const popup = frame.locator('.urPW').first();
        const hasPopup = await popup.isVisible({ timeout: 2000 }).catch(() => false);

        if (hasPopup) {
            console.log('\n✓ Popup appeared!');

            const title = await frame.locator('.urPWTitle').innerText().catch(() => '');
            console.log('  Title:', title);

            // Fill project name
            console.log('  Entering: Z_CRP_SRV');
            const input = frame.locator('.urPW input[type="text"]').first();
            await input.fill('Z_CRP_SRV');
            await page.keyboard.press('Enter');
            await page.waitForTimeout(4000);

            console.log('✓ Project opened\n');
        } else {
            console.log('\n⚠️ No popup appeared');
            console.log('Trying direct navigation via command field...\n');

            // Navigate fresh to SEGW
            const cmdField = frame.locator('#ToolbarOkCode').first();
            await cmdField.click();
            await cmdField.fill('/nSEGW');
            await page.keyboard.press('Enter');
            await page.waitForTimeout(3000);

            // Now check for popup again
            const popup2 = frame.locator('.urPW').first();
            const hasPopup2 = await popup2.isVisible({ timeout: 2000 }).catch(() => false);

            if (hasPopup2) {
                console.log('✓ Popup after fresh navigation');
                const input2 = frame.locator('.urPW input[type="text"]').first();
                await input2.fill('Z_CRP_SRV');
                await page.keyboard.press('Enter');
                await page.waitForTimeout(4000);
                console.log('✓ Project opened\n');
            }
        }

        // Verify toolbar is now visible
        await page.waitForTimeout(2000);
        const toolbar = frame.locator('#C109_btn0').first();
        const hasToolbar = await toolbar.isVisible({ timeout: 3000 }).catch(() => false);

        await page.screenshot({ path: '05_after_open.png', fullPage: true });

        console.log('========================================');
        console.log('Verification:');
        console.log('========================================');
        console.log('SEGW Toolbar (C109):', hasToolbar ? '✓ VISIBLE' : '✗ NOT VISIBLE');

        if (hasToolbar) {
            console.log('\n✓✓✓ SUCCESS - Ready for framework test! ✓✓✓');
        } else {
            console.log('\n⚠️ Still not in correct screen. May need manual intervention.');
        }

    } catch (error) {
        console.error('\n✗ Error:', error.message);
        throw error;
    }
}

openProjectSegw().catch(console.error);
