/**
 * SegwAutomation.js
 * SEGW (SAP Gateway Service Builder) automation using SAP WebGUI Core Framework
 *
 * This is an example of a transaction-specific module that uses the generic framework.
 * No hardcoded tree navigation or popup handling - all reusable primitives.
 *
 * Usage:
 * ```javascript
 * const { SapConnection } = require('../sap-webgui-core');
 * const SegwAutomation = require('./SegwAutomation');
 *
 * const conn = await SapConnection.connect();
 * const segw = new SegwAutomation(conn);
 *
 * await segw.createEntity('CrpCertificate', false);
 * await segw.addProperties('CrpCertificate', properties);
 * ```
 */

const {
    SapTree,
    SapToolbar,
    SapPopup,
    SapSession,
    SapMenu
} = require('../sap-webgui-core');

class SegwAutomation {
    constructor(connection) {
        this.conn = connection;
        this.frame = connection.frame;
        this.page = connection.page;

        // Initialize framework components
        this.tree = new SapTree(this.frame, this.page);
        this.toolbar = new SapToolbar(this.frame, this.page, 'C109'); // SEGW toolbar prefix
        this.popup = new SapPopup(this.frame, this.page);
        this.session = new SapSession(this.frame, this.page, 'C109');
        this.menu = new SapMenu(this.frame, this.page);

        this.projectName = null;
    }

    /**
     * Set current project context
     * @param {string} projectName - SEGW project name (e.g., 'Z_CRP_SRV')
     */
    setProject(projectName) {
        this.projectName = projectName;
        console.log('[SegwAutomation] Project set to:', projectName);
    }

    /**
     * Create a new entity type
     * @param {string} entityName - Entity name (e.g., 'CrpCertificate')
     * @param {boolean} isMedia - Whether entity is a media entity
     * @param {boolean} createEntitySet - Whether to auto-create entity set
     */
    async createEntity(entityName, isMedia = false, createEntitySet = false) {
        console.log(`[SegwAutomation] Creating entity: ${entityName} (media: ${isMedia})`);

        if (!this.projectName) {
            throw new Error('Project name not set. Call setProject() first.');
        }

        // Step 1: Navigate to Entity Types node
        await this.tree.selectNode([this.projectName, 'Data Model', 'Entity Types']);

        // Step 2: Ensure in Change mode
        await this.session.ensureChangeMode();

        // Step 3: Click Create button (select-then-toolbar pattern)
        await this.toolbar.clickCreate();

        // Step 4: Handle Entity Type popup
        const popupAppeared = await this.popup.waitForPopup(3000);

        if (!popupAppeared) {
            console.error('[SegwAutomation] Entity creation popup did not appear');
            return false;
        }

        // Fill entity name
        await this.popup.fillFirst(entityName);

        // Handle media checkbox if requested
        if (isMedia) {
            await this.popup.setCheckbox('Media', true);
        }

        // Handle "Create Related Entity Set" checkbox
        if (!createEntitySet) {
            // Uncheck it (it's usually checked by default)
            await this.popup.setCheckbox('first', false);
        }

        // Confirm popup
        await this.popup.confirm();

        // Step 5: Handle transport request
        await this.session.handleTransportRequest();

        console.log(`[SegwAutomation] ✓ Entity created: ${entityName}`);
        return true;
    }

    /**
     * Add properties to an entity
     * @param {string} entityName - Entity name
     * @param {Array} properties - Array of property definitions
     * Example property: { name: 'CompanyCode', type: 'Edm.String', key: true, nullable: false, maxLength: 4, label: 'Company Code' }
     */
    async addProperties(entityName, properties) {
        console.log(`[SegwAutomation] Adding ${properties.length} properties to ${entityName}`);

        if (!this.projectName) {
            throw new Error('Project name not set. Call setProject() first.');
        }

        // Navigate to Properties node under entity
        await this.tree.selectNode([
            this.projectName,
            'Data Model',
            'Entity Types',
            entityName,
            'Properties'
        ]);

        // Ensure change mode
        await this.session.ensureChangeMode();

        // Add each property using keyboard navigation (most reliable)
        for (const prop of properties) {
            await this._addSingleProperty(prop);
        }

        console.log('[SegwAutomation] ✓ Properties added');
    }

    /**
     * Add a single property using keyboard input
     * @private
     */
    async _addSingleProperty(prop) {
        console.log(`[SegwAutomation]   Adding: ${prop.name}`);

        // Click "Append Row" button (usually btn5 or use shortcut)
        // For now, use F6 shortcut which often works for "Create/Add"
        await this.menu.shortcut('F6', 500);

        // Fill fields using Tab navigation
        await this.menu.type(prop.name);
        await this.menu.tab();

        const type = prop.type || 'Edm.String';
        await this.menu.type(type);
        await this.menu.tab();

        // Key checkbox
        if (prop.key) {
            await this.menu.pressKey('Space');
        }
        await this.menu.tab();

        // Nullable checkbox
        if (prop.nullable === false) {
            // It's usually checked by default, so space to uncheck
            await this.menu.pressKey('Space');
        }
        await this.menu.tab();

        // Max Length
        if (prop.maxLength) {
            await this.menu.type(prop.maxLength.toString());
        }
        await this.menu.tab();

        // Precision and Scale (for Decimal)
        if (type === 'Edm.Decimal') {
            if (prop.precision) {
                await this.menu.type(prop.precision.toString());
            }
            await this.menu.tab();

            if (prop.scale) {
                await this.menu.type(prop.scale.toString());
            }
            await this.menu.tab();
        } else {
            // Skip precision and scale
            await this.menu.tab();
            await this.menu.tab();
        }

        // Internal Name (skip)
        await this.menu.tab();

        // Label
        if (prop.label) {
            await this.menu.type(prop.label);
        }

        // Confirm row
        await this.menu.enter();
        await this.page.waitForTimeout(500);
    }

    /**
     * Create an entity set
     * @param {string} entitySetName - Entity set name (e.g., 'CrpCertificateSet')
     * @param {string} entityTypeName - Associated entity type
     */
    async createEntitySet(entitySetName, entityTypeName) {
        console.log(`[SegwAutomation] Creating entity set: ${entitySetName} → ${entityTypeName}`);

        if (!this.projectName) {
            throw new Error('Project name not set. Call setProject() first.');
        }

        // Navigate to Entity Sets node
        await this.tree.selectNode([this.projectName, 'Data Model', 'Entity Sets']);

        // Ensure change mode
        await this.session.ensureChangeMode();

        // Click Create
        await this.toolbar.clickCreate();

        // Fill popup
        const appeared = await this.popup.waitForPopup();
        if (appeared) {
            await this.popup.fill({
                'Entity Set Name': entitySetName,
                'Entity Type': entityTypeName
            });

            await this.popup.confirm();
            await this.session.handleTransportRequest();
        }

        console.log('[SegwAutomation] ✓ Entity set created');
    }

    /**
     * Generate runtime objects (MPC/DPC classes)
     */
    async generateRuntimeObjects() {
        console.log('[SegwAutomation] Generating runtime objects...');

        // Click Generate button (btn6 in SEGW)
        await this.toolbar.clickButton(6);

        // Wait for generation to complete (check status bar)
        await this.session.waitForStatus('generated', 15000);

        // Handle transport if appears
        await this.session.handleTransportRequest();

        console.log('[SegwAutomation] ✓ Runtime objects generated');
    }

    /**
     * Save current work
     */
    async save() {
        console.log('[SegwAutomation] Saving...');
        await this.session.save(true); // Auto-handle transport
        console.log('[SegwAutomation] ✓ Saved');
    }

    /**
     * Get status bar message
     */
    async getStatus() {
        return await this.session.getStatusBarMessage();
    }

    /**
     * Take screenshot for debugging
     * @param {string} name - Screenshot name
     */
    async screenshot(name) {
        return await this.conn.screenshot(`segw_${name}`);
    }
}

module.exports = SegwAutomation;
