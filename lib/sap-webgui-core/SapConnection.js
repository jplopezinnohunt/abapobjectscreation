/**
 * SapConnection.js
 * Core connection management for SAP WebGUI automation
 *
 * Handles:
 * - CDP connection to existing Chrome instance
 * - SAP page detection
 * - IFrame context management
 * - Session validation
 */

const { chromium } = require('playwright');

class SapConnection {
    constructor(browser, page, frame) {
        this.browser = browser;
        this.page = page;
        this.frame = frame;
        this._connected = true;
    }

    /**
     * Connect to existing Chrome instance with SAP session
     * @param {string} cdpUrl - Chrome DevTools Protocol URL
     * @param {object} options - Connection options
     * @returns {Promise<SapConnection>}
     */
    static async connect(cdpUrl = 'http://localhost:9222', options = {}) {
        const {
            transactionCode = null,
            timeout = 10000,
            viewport = { width: 1920, height: 1080 }
        } = options;

        console.log('[SapConnection] Connecting to CDP:', cdpUrl);

        try {
            // Connect to existing browser
            const browser = await chromium.connectOverCDP(cdpUrl);
            const contexts = browser.contexts();

            if (contexts.length === 0) {
                throw new Error('No browser contexts found. Is Chrome running with --remote-debugging-port=9222?');
            }

            const context = contexts[0];
            let page;

            // Find SAP page
            if (transactionCode) {
                console.log(`[SapConnection] Looking for page with transaction: ${transactionCode}`);
                page = context.pages().find(p =>
                    p.url().includes('webgui') && p.url().includes(transactionCode.toUpperCase())
                );
            }

            if (!page) {
                console.log('[SapConnection] Looking for any SAP WebGUI page');
                page = context.pages().find(p => p.url().includes('webgui'));
            }

            if (!page) {
                // Use first page as fallback
                page = context.pages()[0];
                console.log('[SapConnection] No SAP page found, using first page:', page.url());
            }

            // Set viewport
            await page.setViewportSize(viewport);

            // Find the main content iframe
            console.log('[SapConnection] Locating SAP content iframe...');
            const frame = await this._findSapFrame(page, timeout);

            console.log('[SapConnection] ✓ Connected successfully');
            return new SapConnection(browser, page, frame);

        } catch (error) {
            console.error('[SapConnection] Connection failed:', error.message);
            throw error;
        }
    }

    /**
     * Find the SAP WebGUI content iframe
     * @private
     */
    static async _findSapFrame(page, timeout) {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const frames = page.frames();

            // Look for itsframe1_ pattern (most common)
            let frame = frames.find(f => f.name().startsWith('itsframe1_'));

            if (frame) {
                console.log('[SapConnection] Found frame:', frame.name());
                return frame;
            }

            // Fallback: look for any frame with SAP-like content
            for (const f of frames) {
                if (f.url().includes('sap') || f.url().includes('its')) {
                    console.log('[SapConnection] Found SAP frame by URL:', f.url());
                    return f;
                }
            }

            // Wait and retry
            await page.waitForTimeout(500);
        }

        // If no frame found, use main page
        console.warn('[SapConnection] No iframe found, using main page');
        return page.mainFrame();
    }

    /**
     * Wait for SAP system to be idle (no busy indicators)
     * @param {number} timeout - Max wait time in ms
     */
    async waitForIdle(timeout = 5000) {
        console.log('[SapConnection] Waiting for SAP to be idle...');

        try {
            // Wait for common SAP busy indicators to disappear
            await this.frame.waitForSelector('.urBusyIndicator', {
                state: 'hidden',
                timeout
            }).catch(() => {});

            await this.frame.waitForSelector('#BUSY', {
                state: 'hidden',
                timeout
            }).catch(() => {});

            // Additional wait for stability
            await this.page.waitForTimeout(500);

            console.log('[SapConnection] ✓ System idle');
        } catch (error) {
            console.warn('[SapConnection] Could not confirm idle state:', error.message);
        }
    }

    /**
     * Get current transaction code from page
     */
    async getCurrentTransaction() {
        try {
            const txInput = await this.page.locator('input[name="~transaction"]').first();
            if (await txInput.isVisible()) {
                return await txInput.getAttribute('value');
            }
        } catch (error) {
            console.warn('[SapConnection] Could not detect transaction:', error.message);
        }
        return null;
    }

    /**
     * Navigate to transaction code
     * @param {string} tcode - Transaction code (e.g., 'SEGW', 'SE11')
     */
    async navigateToTransaction(tcode) {
        console.log(`[SapConnection] Navigating to transaction: ${tcode}`);

        // LEARNING #7: Remove block layer if present (from previous operations)
        await this._removeBlockLayer();

        // LEARNING #1, #3: Command field is in frame, use ToolbarOkCode
        const commandFieldSelectors = [
            '#ToolbarOkCode',           // Primary - confirmed in testing
            'input[name="~command"]',   // Fallback
            'input[id*="command"]',     // Alternative
            '#sap-user-input'           // Legacy
        ];

        let commandField = null;

        // Try frame first
        for (const selector of commandFieldSelectors) {
            try {
                const field = this.frame.locator(selector).first();
                if (await field.isVisible({ timeout: 1000 })) {
                    commandField = field;
                    console.log(`[SapConnection] Found command field: ${selector}`);
                    break;
                }
            } catch (e) {
                // Try next selector
            }
        }

        // Fallback to page if not in frame
        if (!commandField) {
            for (const selector of commandFieldSelectors) {
                try {
                    const field = this.page.locator(selector).first();
                    if (await field.isVisible({ timeout: 1000 })) {
                        commandField = field;
                        console.log(`[SapConnection] Found command field in page: ${selector}`);
                        break;
                    }
                } catch (e) {
                    // Try next selector
                }
            }
        }

        if (!commandField) {
            throw new Error('Command field not found in frame or page');
        }

        await commandField.click();
        await commandField.fill(`/n${tcode}`);
        await this.page.keyboard.press('Enter');

        // Wait for navigation
        await this.waitForIdle();
        await this.page.waitForTimeout(2000);

        console.log(`[SapConnection] ✓ Navigated to ${tcode}`);
    }

    /**
     * Remove block layer if present (internal helper)
     * LEARNING #7: Block layer can persist from previous operations
     * LEARNING #8: Block layer can be in frame OR page context
     * @private
     */
    async _removeBlockLayer() {
        try {
            // Try removing from FRAME first (most likely location)
            const removedFromFrame = await this.frame.evaluate(() => {
                const blocker = document.querySelector('#urPopupWindowBlockLayer');
                if (blocker) {
                    blocker.remove();
                    return true;
                }
                return false;
            }).catch(() => false);

            // Also try removing from main PAGE
            const removedFromPage = await this.page.evaluate(() => {
                const blocker = document.querySelector('#urPopupWindowBlockLayer');
                if (blocker) {
                    blocker.remove();
                    return true;
                }
                return false;
            }).catch(() => false);

            if (removedFromFrame || removedFromPage) {
                console.log(`[SapConnection] Removed block layer from ${removedFromFrame ? 'frame' : 'page'}`);
                await this.page.waitForTimeout(500);
            }
        } catch (error) {
            // Ignore errors - block layer may not exist
        }
    }

    /**
     * Take screenshot for debugging
     * @param {string} name - Screenshot filename
     */
    async screenshot(name) {
        const path = `debug_${name}_${Date.now()}.png`;
        await this.page.screenshot({ path, fullPage: true });
        console.log(`[SapConnection] Screenshot saved: ${path}`);
        return path;
    }

    /**
     * Get status bar message
     */
    async getStatusBarMessage() {
        try {
            const statusBar = this.frame.locator('.urStatusbar, #stbar-msg-txt').first();
            if (await statusBar.isVisible()) {
                const text = await statusBar.innerText();
                return text.trim();
            }
        } catch (error) {
            console.warn('[SapConnection] Could not read status bar:', error.message);
        }
        return null;
    }

    /**
     * Check if connection is still valid
     */
    isConnected() {
        return this._connected && !this.browser.isConnected();
    }

    /**
     * Close connection
     */
    async close() {
        console.log('[SapConnection] Closing connection');
        this._connected = false;
        await this.browser.close();
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapConnection]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapConnection;
