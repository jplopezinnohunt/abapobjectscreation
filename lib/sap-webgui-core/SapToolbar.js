/**
 * SapToolbar.js
 * Generic toolbar interaction for SAP WebGUI
 *
 * Key finding from experiments:
 * - SELECT NODE + CLICK TOOLBAR BUTTON is the most reliable pattern
 * - Toolbar buttons are context-sensitive (act on selected tree node)
 * - ID pattern: C{container}_btn{index}
 * - Tooltip/title attribute is more stable than visual position
 *
 * Handles:
 * - Clicking toolbar buttons by index
 * - Clicking toolbar buttons by tooltip/title
 * - Detecting button state (enabled/disabled)
 * - Context-sensitive operations
 */

class SapToolbar {
    constructor(frame, page, toolbarPrefix = 'C109') {
        this.frame = frame;
        this.page = page;
        this.toolbarPrefix = toolbarPrefix;
    }

    /**
     * Click a toolbar button by its index
     * @param {number} index - Button index (e.g., 0 for btn0)
     * @param {object} options - Click options
     */
    async clickButton(index, options = {}) {
        const {
            waitAfter = 1000,
            force = true
        } = options;

        const buttonId = `${this.toolbarPrefix}_btn${index}`;
        console.log(`[SapToolbar] Clicking button: ${buttonId}`);

        try {
            // Try button itself
            const button = this.frame.locator(`#${buttonId}`).first();

            if (await button.isVisible({ timeout: 2000 })) {
                await button.click({ force });
                await this.page.waitForTimeout(waitAfter);
                console.log(`[SapToolbar] ✓ Clicked: ${buttonId}`);
                return true;
            }

            // Try button image (some buttons use img elements)
            const buttonImg = this.frame.locator(`#${buttonId}-img`).first();

            if (await buttonImg.isVisible({ timeout: 1000 })) {
                await buttonImg.click({ force });
                await this.page.waitForTimeout(waitAfter);
                console.log(`[SapToolbar] ✓ Clicked: ${buttonId}-img`);
                return true;
            }

            console.warn(`[SapToolbar] Button not found or not visible: ${buttonId}`);
            return false;

        } catch (error) {
            console.error(`[SapToolbar] Error clicking button ${buttonId}:`, error.message);
            return false;
        }
    }

    /**
     * Click a toolbar button by its tooltip/title
     * @param {string} tooltip - Button tooltip text (e.g., "Create", "Save", "Generate")
     * @param {object} options - Click options
     */
    async clickButtonByTooltip(tooltip, options = {}) {
        const {
            waitAfter = 1000,
            force = true,
            exactMatch = false
        } = options;

        console.log(`[SapToolbar] Looking for button with tooltip: "${tooltip}"`);

        try {
            // Build selector
            let selector;
            if (exactMatch) {
                selector = `[title="${tooltip}"]`;
            } else {
                selector = `[title*="${tooltip}"]`;
            }

            // Look for button or image with title
            const button = this.frame.locator(`${selector}, img${selector}`).first();

            if (await button.isVisible({ timeout: 2000 })) {
                const actualTitle = await button.getAttribute('title');
                console.log(`[SapToolbar]   Found button: "${actualTitle}"`);

                await button.click({ force });
                await this.page.waitForTimeout(waitAfter);

                console.log(`[SapToolbar] ✓ Clicked button by tooltip`);
                return true;
            }

            console.warn(`[SapToolbar] Button not found with tooltip: "${tooltip}"`);
            return false;

        } catch (error) {
            console.error(`[SapToolbar] Error clicking button by tooltip:`, error.message);
            return false;
        }
    }

    /**
     * Get button state (enabled/disabled/active)
     * @param {number} index - Button index
     * @returns {Promise<string>} - 'enabled', 'disabled', 'active', or 'not_found'
     */
    async getButtonState(index) {
        const buttonId = `${this.toolbarPrefix}_btn${index}`;

        try {
            const button = this.frame.locator(`#${buttonId}`).first();

            if (!(await button.isVisible({ timeout: 500 }))) {
                return 'not_found';
            }

            const classes = await button.getAttribute('class') || '';
            const disabled = await button.getAttribute('disabled');

            if (disabled !== null || classes.includes('disabled')) {
                return 'disabled';
            }

            if (classes.includes('active') || classes.includes('pressed')) {
                return 'active';
            }

            return 'enabled';

        } catch (error) {
            return 'not_found';
        }
    }

    /**
     * Get button tooltip/title
     * @param {number} index - Button index
     * @returns {Promise<string|null>}
     */
    async getButtonTooltip(index) {
        const buttonId = `${this.toolbarPrefix}_btn${index}`;

        try {
            const button = this.frame.locator(`#${buttonId}`).first();

            if (await button.isVisible({ timeout: 500 })) {
                return await button.getAttribute('title');
            }

            return null;

        } catch (error) {
            return null;
        }
    }

    /**
     * Wait for a button to become enabled
     * @param {number} index - Button index
     * @param {number} timeout - Max wait time in ms
     */
    async waitForButtonEnabled(index, timeout = 5000) {
        const buttonId = `${this.toolbarPrefix}_btn${index}`;
        console.log(`[SapToolbar] Waiting for button to be enabled: ${buttonId}`);

        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const state = await this.getButtonState(index);

            if (state === 'enabled' || state === 'active') {
                console.log(`[SapToolbar] ✓ Button enabled: ${buttonId}`);
                return true;
            }

            await this.page.waitForTimeout(500);
        }

        console.warn(`[SapToolbar] Timeout waiting for button: ${buttonId}`);
        return false;
    }

    /**
     * Check if a button exists and is visible
     * @param {number} index - Button index
     */
    async isButtonVisible(index) {
        const buttonId = `${this.toolbarPrefix}_btn${index}`;

        try {
            const button = this.frame.locator(`#${buttonId}`).first();
            return await button.isVisible({ timeout: 1000 });
        } catch (error) {
            return false;
        }
    }

    /**
     * List all visible buttons in toolbar with their tooltips
     * Useful for debugging
     */
    async listButtons() {
        console.log(`[SapToolbar] Listing all buttons for prefix: ${this.toolbarPrefix}`);

        const buttons = [];

        for (let i = 0; i < 20; i++) {
            const buttonId = `${this.toolbarPrefix}_btn${i}`;
            const button = this.frame.locator(`#${buttonId}`).first();

            try {
                if (await button.isVisible({ timeout: 500 })) {
                    const tooltip = await button.getAttribute('title');
                    const state = await this.getButtonState(i);

                    buttons.push({
                        index: i,
                        id: buttonId,
                        tooltip,
                        state
                    });

                    console.log(`[SapToolbar]   [${i}] ${tooltip || 'No tooltip'} (${state})`);
                }
            } catch (error) {
                // Button doesn't exist, skip
            }
        }

        return buttons;
    }

    /**
     * Click Create button (btn0 - most common context-sensitive button)
     * Convenience method for the most-used pattern
     */
    async clickCreate() {
        console.log('[SapToolbar] Clicking Create button (btn0)');
        return await this.clickButton(0);
    }

    /**
     * Click Save button (varies by transaction, try common indices)
     * @param {number[]} tryIndices - Button indices to try (e.g., [2, 11])
     */
    async clickSave(tryIndices = [11, 2, 1]) {
        console.log('[SapToolbar] Looking for Save button');

        for (const index of tryIndices) {
            const tooltip = await this.getButtonTooltip(index);

            if (tooltip && tooltip.toLowerCase().includes('save')) {
                console.log(`[SapToolbar] Found Save at btn${index}`);
                return await this.clickButton(index);
            }
        }

        // Fallback: use keyboard
        console.log('[SapToolbar] Save button not found, using Ctrl+S');
        await this.page.keyboard.press('Control+s');
        await this.page.waitForTimeout(1000);
        return true;
    }

    /**
     * Change toolbar prefix (for different screens)
     * @param {string} prefix - New prefix (e.g., 'C109', 'C110')
     */
    setPrefix(prefix) {
        console.log(`[SapToolbar] Changing prefix: ${this.toolbarPrefix} → ${prefix}`);
        this.toolbarPrefix = prefix;
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapToolbar]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapToolbar;
