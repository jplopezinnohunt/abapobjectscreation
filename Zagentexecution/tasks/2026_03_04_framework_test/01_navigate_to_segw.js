/**
 * 01_navigate_to_segw.js
 * Navigate from SAP Easy Access to SEGW and open Z_CRP_SRV project
 *
 * Learning: Test the framework's navigation capabilities
 */

const { SapConnection } = require('../../../lib/sap-webgui-core');

async function navigateToSegw() {
    console.log('========================================');
    console.log('Step 1: Navigate to SEGW');
    console.log('========================================\n');

    let conn;

    try {
        // Connect to current SAP session
        console.log('Connecting to SAP session...');
        conn = await SapConnection.connect('http://localhost:9222');
        console.log('✓ Connected\n');

        // Take initial screenshot
        await conn.screenshot('01_initial_state');
        console.log('✓ Initial screenshot taken\n');

        // Navigate to SEGW
        console.log('Navigating to SEGW transaction...');
        await conn.navigateToTransaction('SEGW');
        console.log('✓ Navigation command sent\n');

        // Wait for page to load
        await conn.waitForIdle();
        console.log('✓ Page loaded\n');

        // Take screenshot after navigation
        await conn.screenshot('02_segw_loaded');
        console.log('✓ SEGW screenshot taken\n');

        // Check if we need to open project
        console.log('Checking for project open dialog...');
        await conn.page.waitForTimeout(2000);

        // Try to detect "Open Project" popup
        const hasPopup = await conn.frame.locator('.urPW').isVisible({ timeout: 2000 }).catch(() => false);

        if (hasPopup) {
            console.log('✓ Open Project dialog detected\n');
            console.log('Entering project name: Z_CRP_SRV...');

            // Fill project name
            const input = conn.frame.locator('.urPW input[type="text"]').first();
            await input.fill('Z_CRP_SRV');
            await conn.page.keyboard.press('Enter');
            await conn.page.waitForTimeout(3000);

            console.log('✓ Project opened\n');
        } else {
            console.log('ℹ No Open Project dialog - project may already be loaded\n');
        }

        // Take final screenshot
        await conn.screenshot('03_project_ready');
        console.log('✓ Final screenshot taken\n');

        // Get current status
        const status = await conn.getStatusBarMessage();
        if (status) {
            console.log('Status Bar:', status, '\n');
        }

        console.log('========================================');
        console.log('✓✓✓ Navigation Successful ✓✓✓');
        console.log('========================================\n');
        console.log('SEGW is ready for testing!');
        console.log('Project Z_CRP_SRV should be loaded.\n');

        // Don't close - leave open for next test
        console.log('Browser left open for next step...');

    } catch (error) {
        console.error('\n========================================');
        console.error('✗✗✗ Navigation Failed ✗✗✗');
        console.error('========================================');
        console.error('\nError:', error.message);
        console.error('Stack:', error.stack);

        if (conn) {
            await conn.screenshot('navigation_error');
        }

        process.exit(1);
    }
}

navigateToSegw().catch(console.error);
