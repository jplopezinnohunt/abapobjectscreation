/**
 * SapPopup.js
 * Generic popup/dialog handling for SAP WebGUI
 *
 * Key findings:
 * - SAP popups consistently use class .urPW
 * - Title is in .urPWTitle
 * - First text input is usually the main field
 * - Enter key or green check button confirms
 * - Escape key or red X cancels
 *
 * Handles:
 * - Popup detection and waiting
 * - Title extraction
 * - Field filling (by order or label)
 * - Confirmation/cancellation
 * - Checkbox handling
 */

class SapPopup {
    constructor(frame, page) {
        this.frame = frame;
        this.page = page;
        this.currentPopup = null;
    }

    /**
     * Wait for popup to appear
     * @param {number} timeout - Max wait time in ms
     * @returns {Promise<boolean>} - True if popup appeared
     */
    async waitForPopup(timeout = 5000) {
        console.log('[SapPopup] Waiting for popup...');

        try {
            // LEARNING #5: Check for block layer first (indicates popup is loading)
            const blockLayer = this.frame.locator('#urPopupWindowBlockLayer').first();
            const hasBlocker = await blockLayer.isVisible({ timeout: 1000 }).catch(() => false);

            if (hasBlocker) {
                console.log('[SapPopup] Block layer detected, waiting for popup to render...');
                // Wait longer when block layer is present
                await this.page.waitForTimeout(1500);
            }

            const popup = this.frame.locator('.urPW').first();
            await popup.waitFor({ state: 'visible', timeout });

            this.currentPopup = popup;
            console.log('[SapPopup] ✓ Popup appeared');
            return true;

        } catch (error) {
            console.warn('[SapPopup] No popup appeared within timeout');
            return false;
        }
    }

    /**
     * Check if popup is currently visible
     * @returns {Promise<boolean>}
     */
    async isVisible() {
        try {
            const popup = this.frame.locator('.urPW').first();
            return await popup.isVisible({ timeout: 500 });
        } catch (error) {
            return false;
        }
    }

    /**
     * Get popup title
     * @returns {Promise<string|null>}
     */
    async getTitle() {
        try {
            const title = this.frame.locator('.urPWTitle').first();

            if (await title.isVisible({ timeout: 1000 })) {
                const text = await title.innerText();
                console.log('[SapPopup] Title:', text);
                return text.trim();
            }

            return null;

        } catch (error) {
            console.warn('[SapPopup] Could not get title:', error.message);
            return null;
        }
    }

    /**
     * Fill popup fields by order
     * @param {string[]} values - Array of values to fill in order
     */
    async fillByOrder(values) {
        console.log('[SapPopup] Filling fields by order:', values);

        const popup = this.frame.locator('.urPW').first();
        const inputs = popup.locator('input[type="text"]');

        const count = await inputs.count();
        console.log(`[SapPopup] Found ${count} text input(s)`);

        for (let i = 0; i < Math.min(count, values.length); i++) {
            if (values[i] !== null && values[i] !== undefined) {
                const input = inputs.nth(i);
                await input.fill(values[i]);
                console.log(`[SapPopup]   [${i}] Filled: "${values[i]}"`);
                await this.page.waitForTimeout(200);
            }
        }

        console.log('[SapPopup] ✓ Fields filled');
    }

    /**
     * Fill popup fields by label (more robust)
     * @param {Object} fieldMap - Map of label → value
     * Example: { 'Entity Type Name': 'CrpCertificate', 'Description': 'My desc' }
     */
    async fill(fieldMap) {
        console.log('[SapPopup] Filling fields by label:', Object.keys(fieldMap));

        const popup = this.frame.locator('.urPW').first();

        for (const [label, value] of Object.entries(fieldMap)) {
            if (value === null || value === undefined) continue;

            try {
                // Strategy 1: Find label and get associated input
                let input = popup.locator(`label:has-text("${label}")`).first()
                    .locator('..') // parent
                    .locator('input[type="text"]').first();

                if (!(await input.isVisible({ timeout: 500 }))) {
                    // Strategy 2: Find by title attribute
                    input = popup.locator(`input[title="${label}"]`).first();
                }

                if (!(await input.isVisible({ timeout: 500 }))) {
                    // Strategy 3: Find by placeholder
                    input = popup.locator(`input[placeholder*="${label}"]`).first();
                }

                if (await input.isVisible({ timeout: 500 })) {
                    await input.fill(value);
                    console.log(`[SapPopup]   "${label}" → "${value}"`);
                    await this.page.waitForTimeout(200);
                } else {
                    console.warn(`[SapPopup]   Field not found: "${label}"`);
                }

            } catch (error) {
                console.warn(`[SapPopup]   Could not fill "${label}":`, error.message);
            }
        }

        console.log('[SapPopup] ✓ Fields filled by label');
    }

    /**
     * Fill first text input (common case)
     * @param {string} value - Value to fill
     */
    async fillFirst(value) {
        console.log('[SapPopup] Filling first input:', value);

        const popup = this.frame.locator('.urPW').first();
        const input = popup.locator('input[type="text"]').first();

        await input.fill(value);
        await this.page.waitForTimeout(200);

        console.log('[SapPopup] ✓ First input filled');
    }

    /**
     * Check/uncheck a checkbox in popup
     * @param {string} label - Checkbox label (or use 'first' for first checkbox)
     * @param {boolean} checked - True to check, false to uncheck
     */
    async setCheckbox(label, checked) {
        console.log(`[SapPopup] ${checked ? 'Checking' : 'Unchecking'} checkbox: ${label}`);

        const popup = this.frame.locator('.urPW').first();
        let checkbox;

        if (label === 'first') {
            checkbox = popup.locator('input[type="checkbox"]').first();
        } else {
            // Find by associated label
            checkbox = popup.locator(`label:has-text("${label}")`)
                .locator('..')
                .locator('input[type="checkbox"]').first();
        }

        if (await checkbox.isVisible({ timeout: 1000 })) {
            const isChecked = await checkbox.isChecked();

            if (isChecked !== checked) {
                await checkbox.click({ force: true });
                console.log('[SapPopup] ✓ Checkbox toggled');
            } else {
                console.log('[SapPopup] ✓ Checkbox already in desired state');
            }
        } else {
            console.warn('[SapPopup] Checkbox not found:', label);
        }
    }

    /**
     * Confirm popup (Enter key or green check button)
     * @param {object} options - Confirmation options
     */
    async confirm(options = {}) {
        const {
            method = 'keyboard', // 'keyboard' or 'button'
            waitAfter = 2000
        } = options;

        console.log(`[SapPopup] Confirming popup (method: ${method})`);

        if (method === 'keyboard') {
            await this.page.keyboard.press('Enter');
        } else {
            // Try to find green check / OK button
            const confirmButtons = [
                '[title="Continue"]',
                '[title="OK"]',
                '[title="Confirm"]',
                '.urPW [id$="btn[0]"]',
                '.urPW img[title*="Continue"]'
            ];

            let clicked = false;
            for (const selector of confirmButtons) {
                try {
                    const button = this.frame.locator(selector).first();
                    if (await button.isVisible({ timeout: 500 })) {
                        await button.click({ force: true });
                        clicked = true;
                        break;
                    }
                } catch (error) {
                    // Try next selector
                }
            }

            if (!clicked) {
                console.warn('[SapPopup] Confirm button not found, using Enter key');
                await this.page.keyboard.press('Enter');
            }
        }

        await this.page.waitForTimeout(waitAfter);
        this.currentPopup = null;

        console.log('[SapPopup] ✓ Popup confirmed');
    }

    /**
     * Cancel popup (Escape key or red X button)
     * @param {object} options - Cancellation options
     */
    async cancel(options = {}) {
        const {
            method = 'keyboard', // 'keyboard' or 'button'
            waitAfter = 1000
        } = options;

        console.log(`[SapPopup] Cancelling popup (method: ${method})`);

        if (method === 'keyboard') {
            await this.page.keyboard.press('Escape');
        } else {
            // Try to find red X / Cancel button
            const cancelButtons = [
                '[title="Cancel"]',
                '[title="Close"]',
                '.urPW [id$="btn[1]"]',
                '.urPW img[title*="Cancel"]'
            ];

            let clicked = false;
            for (const selector of cancelButtons) {
                try {
                    const button = this.frame.locator(selector).first();
                    if (await button.isVisible({ timeout: 500 })) {
                        await button.click({ force: true });
                        clicked = true;
                        break;
                    }
                } catch (error) {
                    // Try next selector
                }
            }

            if (!clicked) {
                console.warn('[SapPopup] Cancel button not found, using Escape key');
                await this.page.keyboard.press('Escape');
            }
        }

        await this.page.waitForTimeout(waitAfter);
        this.currentPopup = null;

        console.log('[SapPopup] ✓ Popup cancelled');
    }

    /**
     * Dismiss popup (works for both confirm and cancel)
     * Uses Enter by default
     */
    async dismiss() {
        console.log('[SapPopup] Dismissing popup');
        await this.confirm();
    }

    /**
     * Get all text from popup (for debugging)
     */
    async getText() {
        try {
            const popup = this.frame.locator('.urPW').first();
            if (await popup.isVisible({ timeout: 500 })) {
                return await popup.innerText();
            }
            return null;
        } catch (error) {
            return null;
        }
    }

    /**
     * Wait for popup to disappear
     * @param {number} timeout - Max wait time in ms
     */
    async waitForClose(timeout = 5000) {
        console.log('[SapPopup] Waiting for popup to close...');

        try {
            const popup = this.frame.locator('.urPW').first();
            await popup.waitFor({ state: 'hidden', timeout });

            console.log('[SapPopup] ✓ Popup closed');
            return true;

        } catch (error) {
            console.warn('[SapPopup] Popup did not close within timeout');
            return false;
        }
    }

    /**
     * Handle popup with automatic field filling and confirmation
     * Convenience method for simple popups
     * @param {Object} fields - Field map or array of values
     */
    async handle(fields, options = {}) {
        const {
            checkTitle = null,
            uncheckFirst = false,
            confirmMethod = 'keyboard'
        } = options;

        console.log('[SapPopup] Handling popup automatically');

        // Wait for popup
        const appeared = await this.waitForPopup();
        if (!appeared) {
            console.warn('[SapPopup] No popup to handle');
            return false;
        }

        // Check title if specified
        if (checkTitle) {
            const title = await this.getTitle();
            if (title && !title.includes(checkTitle)) {
                console.warn(`[SapPopup] Title mismatch: expected "${checkTitle}", got "${title}"`);
                return false;
            }
        }

        // Fill fields
        if (Array.isArray(fields)) {
            await this.fillByOrder(fields);
        } else if (typeof fields === 'object') {
            await this.fill(fields);
        } else if (typeof fields === 'string') {
            await this.fillFirst(fields);
        }

        // Uncheck first checkbox if requested (common pattern)
        if (uncheckFirst) {
            await this.setCheckbox('first', false);
        }

        // Confirm
        await this.confirm({ method: confirmMethod });

        console.log('[SapPopup] ✓ Popup handled successfully');
        return true;
    }

    /**
     * Dismiss block layer if it persists (emergency use)
     * Usually not needed, but available if popup is stuck
     */
    async dismissBlockLayer() {
        console.log('[SapPopup] Attempting to remove block layer...');
        try {
            await this.page.evaluate(() => {
                const blocker = document.querySelector('#urPopupWindowBlockLayer');
                if (blocker) {
                    blocker.remove();
                    return true;
                }
                return false;
            });
            await this.page.waitForTimeout(500);
            console.log('[SapPopup] ✓ Block layer removed');
        } catch (error) {
            console.warn('[SapPopup] Could not remove block layer:', error.message);
        }
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapPopup]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapPopup;
