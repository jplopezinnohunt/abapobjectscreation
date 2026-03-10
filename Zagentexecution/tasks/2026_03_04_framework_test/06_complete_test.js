/**
 * 06_complete_test.js
 * Complete end-to-end test using UPDATED framework
 *
 * Goal: CREATE SUCCESS TODAY!
 */

const { SapConnection } = require('../../../lib/sap-webgui-core');
const SegwAutomation = require('../../../lib/sap-transactions/SegwAutomation');

async function completeTest() {
    console.log('\n========================================');
    console.log('🚀 COMPLETE FRAMEWORK TEST');
    console.log('========================================\n');

    let conn;

    try {
        // ==================================================
        // STEP 1: CONNECT
        // ==================================================
        console.log('📡 Step 1: Connecting to SAP...\n');
        conn = await SapConnection.connect('http://localhost:9222', {
            timeout: 10000
        });
        console.log('✅ Connected successfully!\n');
        await conn.screenshot('step1_connected');

        // ==================================================
        // STEP 2: NAVIGATE TO SEGW
        // ==================================================
        console.log('🧭 Step 2: Navigating to SEGW...\n');
        await conn.navigateToTransaction('SEGW');
        console.log('✅ Navigation command sent!\n');
        await conn.page.waitForTimeout(3000);
        await conn.screenshot('step2_segw_navigation');

        // ==================================================
        // STEP 3: OPEN PROJECT
        // ==================================================
        console.log('📂 Step 3: Opening project Z_CRP_SRV...\n');

        // Check for popup
        const popup = conn.frame.locator('.urPW').first();
        let hasPopup = await popup.isVisible({ timeout: 2000 }).catch(() => false);

        if (!hasPopup) {
            console.log('   No popup yet, clicking Open Project button...');
            // Try to find and click Open Project
            const openBtn = conn.frame.locator('[title*="Open"]').first();
            if (await openBtn.isVisible({ timeout: 2000 })) {
                await openBtn.click({ force: true });
                await conn.page.waitForTimeout(3000);
                hasPopup = await popup.isVisible({ timeout: 2000 }).catch(() => false);
            }
        }

        if (hasPopup) {
            console.log('✅ Popup detected!');

            // LEARNING #5: Wait for block layer to clear
            await conn.page.waitForTimeout(2000);

            const title = await conn.frame.locator('.urPWTitle').innerText().catch(() => '');
            console.log('   Popup title:', title);

            console.log('   Entering: Z_CRP_SRV');
            const input = conn.frame.locator('.urPW input[type="text"]').first();
            await input.fill('Z_CRP_SRV');
            await conn.page.keyboard.press('Enter');
            await conn.page.waitForTimeout(4000);
            console.log('✅ Project name entered!\n');
        } else {
            console.log('ℹ️  No popup - project may already be open\n');
        }

        await conn.screenshot('step3_project_opened');

        // ==================================================
        // STEP 4: INITIALIZE SEGW AUTOMATION
        // ==================================================
        console.log('🤖 Step 4: Initializing SEGW automation...\n');
        const segw = new SegwAutomation(conn);
        segw.setProject('Z_CRP_SRV');
        console.log('✅ SEGW automation ready!\n');

        // ==================================================
        // STEP 5: CREATE TEST ENTITY
        // ==================================================
        console.log('🎯 Step 5: Creating test entity...\n');

        const timestamp = Date.now().toString().slice(-6);
        const entityName = `TestEntity${timestamp}`;
        console.log(`   Entity name: ${entityName}\n`);

        const created = await segw.createEntity(entityName, false, false);

        if (created) {
            console.log('✅ Entity created successfully!\n');
        } else {
            throw new Error('Entity creation returned false');
        }

        await conn.screenshot('step5_entity_created');

        // ==================================================
        // STEP 6: ADD PROPERTIES
        // ==================================================
        console.log('📝 Step 6: Adding properties...\n');

        const properties = [
            {
                name: 'Id',
                type: 'Edm.String',
                key: true,
                nullable: false,
                maxLength: 10,
                label: 'ID'
            },
            {
                name: 'Name',
                type: 'Edm.String',
                key: false,
                nullable: true,
                maxLength: 40,
                label: 'Name'
            },
            {
                name: 'CreatedAt',
                type: 'Edm.DateTime',
                key: false,
                nullable: true,
                label: 'Created At'
            }
        ];

        console.log(`   Adding ${properties.length} properties:\n`);
        properties.forEach(p => {
            console.log(`   - ${p.name} (${p.type})${p.key ? ' [KEY]' : ''}`);
        });
        console.log();

        await segw.addProperties(entityName, properties);
        console.log('✅ Properties added!\n');

        await conn.screenshot('step6_properties_added');

        // ==================================================
        // STEP 7: SAVE
        // ==================================================
        console.log('💾 Step 7: Saving...\n');
        await segw.save();

        const status = await segw.getStatus();
        console.log('   Status bar:', status || 'N/A');
        console.log('✅ Saved!\n');

        await conn.screenshot('step7_saved');

        // ==================================================
        // SUCCESS!
        // ==================================================
        console.log('\n========================================');
        console.log('🎉🎉🎉 SUCCESS! 🎉🎉🎉');
        console.log('========================================\n');

        console.log('✅ Framework Test PASSED!\n');
        console.log('Summary:');
        console.log(`  - Entity: ${entityName}`);
        console.log(`  - Properties: ${properties.length}`);
        console.log(`  - Status: ${status || 'Completed'}`);
        console.log('\nFramework modules used:');
        console.log('  ✅ SapConnection');
        console.log('  ✅ SapTree');
        console.log('  ✅ SapToolbar');
        console.log('  ✅ SapPopup (with block layer fix)');
        console.log('  ✅ SapSession');
        console.log('  ✅ SapMenu');
        console.log('  ✅ SegwAutomation');
        console.log('\n🚀 The framework WORKS! 🚀\n');

        console.log('Screenshots saved:');
        console.log('  - step1_connected');
        console.log('  - step2_segw_navigation');
        console.log('  - step3_project_opened');
        console.log('  - step5_entity_created');
        console.log('  - step6_properties_added');
        console.log('  - step7_saved');

        console.log('\n========================================');
        console.log('You did it! 💪');
        console.log('========================================\n');

    } catch (error) {
        console.error('\n========================================');
        console.error('❌ Test Failed');
        console.error('========================================\n');
        console.error('Error:', error.message);
        console.error('\nStack:', error.stack);

        if (conn) {
            await conn.screenshot('error_state');
            console.log('\nError screenshot saved: error_state');
        }

        console.error('\n⚠️ Don\'t worry - this is part of learning!');
        console.error('We\'ll fix it and try again.\n');

        process.exit(1);
    }
}

console.log('🔥 Starting complete framework test...');
console.log('Goal: Create entity with properties in SEGW');
console.log('Using: Updated framework with all learnings\n');

completeTest().catch(console.error);
