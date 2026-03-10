/**
 * SapSession.js
 * Session management for SAP WebGUI
 *
 * Handles:
 * - Display <-> Change mode toggle
 * - Transport request handling
 * - Save operations
 * - Status bar reading
 * - Session state management
 */

class SapSession {
    constructor(frame, page, toolbarPrefix = 'C109') {
        this.frame = frame;
        this.page = page;
        this.toolbarPrefix = toolbarPrefix;
        this.inChangeMode = false;
    }

    /**
     * Ensure system is in Change mode (not Display mode)
     * @param {object} options - Mode options
     */
    async ensureChangeMode(options = {}) {
        const {
            toolbarPrefix = this.toolbarPrefix,
            waitAfter = 1000
        } = options;

        console.log('[SapSession] Ensuring Change mode...');

        try {
            // Display <-> Change button is usually btn3
            const toggleButton = this.frame.locator(`#${toolbarPrefix}_btn3`).first();

            if (!(await toggleButton.isVisible({ timeout: 2000 }))) {
                console.log('[SapSession] Toggle button not found, assuming Change mode available');
                this.inChangeMode = true;
                return;
            }

            // Check button title to determine current mode
            const title = await toggleButton.getAttribute('title');
            console.log(`[SapSession] Toggle button title: "${title}"`);

            if (title && (title.includes('Change') || title.includes('Edit'))) {
                // Currently in Display mode, need to switch to Change
                console.log('[SapSession] Switching from Display to Change mode');
                await toggleButton.click({ force: true });
                await this.page.waitForTimeout(waitAfter);
                this.inChangeMode = true;
                console.log('[SapSession] ✓ Now in Change mode');
            } else if (title && title.includes('Display')) {
                // Currently in Change mode already
                console.log('[SapSession] ✓ Already in Change mode');
                this.inChangeMode = true;
            } else {
                console.warn('[SapSession] Could not determine mode from button title');
                this.inChangeMode = true;
            }

        } catch (error) {
            console.warn('[SapSession] Could not toggle mode:', error.message);
            this.inChangeMode = true; // Assume it's okay
        }
    }

    /**
     * Handle transport request popup if it appears
     * @param {object} options - Transport options
     */
    async handleTransportRequest(options = {}) {
        const {
            action = 'continue', // 'continue', 'local', 'create', 'specify'
            transportId = null,
            timeout = 3000,
            waitAfter = 2000
        } = options;

        console.log('[SapSession] Checking for transport request...');

        await this.page.waitForTimeout(1000);

        // Check if transport popup appeared
        const transportPopup = this.frame.locator('.urPW').first();
        const isVisible = await transportPopup.isVisible({ timeout: 1000 }).catch(() => false);

        if (!isVisible) {
            console.log('[SapSession] No transport request');
            return;
        }

        // Check if it's actually a transport popup
        const titleElem = this.frame.locator('.urPWTitle').first();
        let title = '';
        if (await titleElem.isVisible({ timeout: 500 })) {
            title = await titleElem.innerText();
        }

        if (!title.toLowerCase().includes('transport') &&
            !title.toLowerCase().includes('request') &&
            !title.toLowerCase().includes('workbench')) {
            console.log('[SapSession] Popup is not transport-related');
            return;
        }

        console.log('[SapSession] Transport request popup detected:', title);

        if (action === 'continue' || action === 'default') {
            // Just press Enter to accept default
            console.log('[SapSession] Accepting default transport');
            await this.page.keyboard.press('Enter');
            await this.page.waitForTimeout(waitAfter);

        } else if (action === 'local') {
            // Click "Local Object" button
            const localBtn = this.frame.locator('[title*="Local Object"], button:has-text("Local Object")').first();
            if (await localBtn.isVisible({ timeout: 1000 })) {
                await localBtn.click({ force: true });
                console.log('[SapSession] Selected Local Object');
            } else {
                console.warn('[SapSession] Local Object button not found');
                await this.page.keyboard.press('Enter');
            }
            await this.page.waitForTimeout(waitAfter);

        } else if (action === 'specify' && transportId) {
            // Enter specific transport ID
            const input = transportPopup.locator('input[type="text"]').first();
            await input.fill(transportId);
            await this.page.keyboard.press('Enter');
            console.log('[SapSession] Specified transport:', transportId);
            await this.page.waitForTimeout(waitAfter);

        } else if (action === 'create') {
            // Create new transport (usually F5 or a button)
            await this.page.keyboard.press('F5');
            await this.page.waitForTimeout(2000);

            // Fill transport description if new dialog appears
            const descInput = this.frame.locator('.urPW input[type="text"]').first();
            if (await descInput.isVisible({ timeout: 1000 })) {
                await descInput.fill('Automated transport');
                await this.page.keyboard.press('Enter');
                await this.page.waitForTimeout(waitAfter);
            }

            console.log('[SapSession] Created new transport');
        }

        console.log('[SapSession] ✓ Transport request handled');
    }

    /**
     * Save current work (Ctrl+S)
     * @param {boolean} handleTransport - Auto-handle transport if appears
     */
    async save(handleTransport = true) {
        console.log('[SapSession] Saving...');

        await this.page.keyboard.press('Control+s');
        await this.page.waitForTimeout(2000);

        if (handleTransport) {
            await this.handleTransportRequest();
        }

        // Check status bar for confirmation
        const status = await this.getStatusBarMessage();
        if (status) {
            console.log('[SapSession] Status after save:', status);
        }

        console.log('[SapSession] ✓ Save complete');
    }

    /**
     * Get status bar message
     * @returns {Promise<string|null>}
     */
    async getStatusBarMessage() {
        try {
            // Try multiple selectors for status bar
            const selectors = [
                '.urStatusbar',
                '#stbar-msg-txt',
                '[id*="statusbar"]',
                '[class*="statusbar"]'
            ];

            for (const selector of selectors) {
                const statusBar = this.frame.locator(selector).first();

                if (await statusBar.isVisible({ timeout: 500 })) {
                    const text = await statusBar.innerText();
                    return text.trim();
                }
            }

            return null;

        } catch (error) {
            return null;
        }
    }

    /**
     * Wait for status bar to contain specific text
     * @param {string} expectedText - Text to wait for
     * @param {number} timeout - Max wait time in ms
     */
    async waitForStatus(expectedText, timeout = 10000) {
        console.log(`[SapSession] Waiting for status: "${expectedText}"`);

        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const status = await this.getStatusBarMessage();

            if (status && status.includes(expectedText)) {
                console.log('[SapSession] ✓ Status found:', status);
                return true;
            }

            await this.page.waitForTimeout(500);
        }

        console.warn(`[SapSession] Timeout waiting for status: "${expectedText}"`);
        return false;
    }

    /**
     * Check if status bar shows an error
     * @returns {Promise<boolean>}
     */
    async hasError() {
        const status = await this.getStatusBarMessage();

        if (!status) return false;

        const errorIndicators = ['error', 'failed', 'incorrect', 'invalid', 'not authorized'];

        return errorIndicators.some(indicator =>
            status.toLowerCase().includes(indicator)
        );
    }

    /**
     * Check if status bar shows success
     * @returns {Promise<boolean>}
     */
    async hasSuccess() {
        const status = await this.getStatusBarMessage();

        if (!status) return false;

        const successIndicators = ['success', 'saved', 'generated', 'created', 'complete'];

        return successIndicators.some(indicator =>
            status.toLowerCase().includes(indicator)
        );
    }

    /**
     * Execute transaction code
     * @param {string} tcode - Transaction code
     */
    async executeTransaction(tcode) {
        console.log(`[SapSession] Executing transaction: ${tcode}`);

        const commandField = this.page.locator('#sap-user-input, [name="~command"]').first();

        await commandField.click();
        await commandField.fill(`/n${tcode}`);
        await this.page.keyboard.press('Enter');
        await this.page.waitForTimeout(2000);

        console.log(`[SapSession] ✓ Transaction ${tcode} executed`);
    }

    /**
     * Go back (F3)
     */
    async goBack() {
        console.log('[SapSession] Going back (F3)');
        await this.page.keyboard.press('F3');
        await this.page.waitForTimeout(1000);
    }

    /**
     * Exit (Shift+F3 or /nex)
     */
    async exit() {
        console.log('[SapSession] Exiting');
        await this.page.keyboard.press('Shift+F3');
        await this.page.waitForTimeout(1000);
    }

    /**
     * Refresh (F8)
     */
    async refresh() {
        console.log('[SapSession] Refreshing (F8)');
        await this.page.keyboard.press('F8');
        await this.page.waitForTimeout(1500);
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapSession]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapSession;
