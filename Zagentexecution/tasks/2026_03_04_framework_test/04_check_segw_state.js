/**
 * 04_check_segw_state.js
 * Check if SEGW is loaded and what state we're in
 *
 * Learning: Verify SEGW state before proceeding with framework test
 */

const { chromium } = require('playwright');

async function checkSegwState() {
    console.log('========================================');
    console.log('Check SEGW State');
    console.log('========================================\n');

    try {
        const browser = await chromium.connectOverCDP('http://localhost:9222');
        const context = browser.contexts()[0];
        const page = context.pages().find(p => p.url().includes('webgui')) || context.pages()[0];
        const frame = page.frames().find(f => f.name().startsWith('itsframe1_'));

        console.log('Connected. Analyzing current state...\n');

        // Check transaction
        const txField = page.locator('input[name="~transaction"]').first();
        let currentTx = 'Unknown';
        try {
            if (await txField.isVisible({ timeout: 1000 })) {
                currentTx = await txField.getAttribute('value') || 'Unknown';
            }
        } catch (e) {}

        console.log('Current Transaction:', currentTx);

        // Check for SEGW-specific elements
        console.log('\nChecking for SEGW elements...');

        // Look for SEGW tree
        const hasTree = await frame.locator('[id^="tree#"]').first().isVisible({ timeout: 2000 }).catch(() => false);
        console.log('  Tree control:', hasTree ? '✓ Found' : '✗ Not found');

        // Look for SEGW toolbar
        const hasToolbar = await frame.locator('#C109_btn0').first().isVisible({ timeout: 2000 }).catch(() => false);
        console.log('  SEGW Toolbar (C109):', hasToolbar ? '✓ Found' : '✗ Not found');

        // Check for project name in tree
        const hasProject = await frame.locator('span, td').filter({ hasText: /Z_CRP_SRV/ }).first().isVisible({ timeout: 2000 }).catch(() => false);
        console.log('  Project Z_CRP_SRV:', hasProject ? '✓ Found' : '✗ Not found');

        // Check for popup
        const hasPopup = await frame.locator('.urPW').first().isVisible({ timeout: 1000 }).catch(() => false);
        if (hasPopup) {
            const title = await frame.locator('.urPWTitle').innerText().catch(() => '');
            console.log('  Popup:', '✓ Present:', title);
        } else {
            console.log('  Popup:', '✗ None');
        }

        // Take diagnostic screenshot
        await page.screenshot({ path: '04_state_check.png', fullPage: true });
        console.log('\n✓ Screenshot: 04_state_check.png');

        // Summary
        console.log('\n========================================');
        console.log('State Summary:');
        console.log('========================================');
        console.log('Transaction:', currentTx);
        console.log('SEGW Active:', hasTree && hasToolbar ? 'YES' : 'NO');
        console.log('Project Loaded:', hasProject ? 'YES' : 'NO');
        console.log('Ready for Test:', hasTree && hasToolbar && hasProject ? 'YES ✓' : 'NO - Need to open project');

        // Return state for next script
        return {
            isSegw: hasTree && hasToolbar,
            hasProject: hasProject,
            ready: hasTree && hasToolbar && hasProject
        };

    } catch (error) {
        console.error('\n✗ Error:', error.message);
        throw error;
    }
}

checkSegwState()
    .then(state => {
        if (state.ready) {
            console.log('\n✓✓✓ Ready to run framework test! ✓✓✓');
        } else {
            console.log('\n⚠️ Not ready yet. May need to open project manually.');
        }
    })
    .catch(console.error);
