/**
 * SapMenu.js
 * Menu and keyboard shortcut handling for SAP WebGUI
 *
 * Key findings from experiments:
 * - Menu bar (wnd[0]/mbar/menu[X]) is MORE reliable than right-click
 * - Context menus have dynamic IDs and are hard to target
 * - Keyboard shortcuts (F6, Ctrl+S) are most reliable
 * - Use shortcuts > Menu bar > Context menu (in that order of preference)
 *
 * Handles:
 * - Keyboard shortcuts
 * - Menu bar navigation
 * - Context menu (use sparingly)
 */

class SapMenu {
    constructor(frame, page) {
        this.frame = frame;
        this.page = page;

        // Common keyboard shortcuts
        this.shortcuts = {
            save: 'Control+s',
            back: 'F3',
            exit: 'Shift+F3',
            refresh: 'F8',
            create: 'F6',
            delete: 'Shift+F2',
            search: 'Control+f',
            help: 'F1',
            pickList: 'F4'
        };
    }

    /**
     * Trigger a keyboard shortcut
     * @param {string} action - Shortcut name (e.g., 'save', 'create', 'F6')
     * @param {number} waitAfter - Wait time after shortcut
     */
    async shortcut(action, waitAfter = 1000) {
        const key = this.shortcuts[action.toLowerCase()] || action;

        console.log(`[SapMenu] Triggering shortcut: ${key}`);

        await this.page.keyboard.press(key);
        await this.page.waitForTimeout(waitAfter);

        console.log('[SapMenu] ✓ Shortcut executed');
    }

    /**
     * Open menu bar and navigate to item
     * @param {string[]} menuPath - Path through menu (e.g., ['Edit', 'Create'])
     */
    async openMenuBar(menuPath) {
        console.log('[SapMenu] Opening menu bar:', menuPath.join(' → '));

        const menuNames = ['Project', 'Edit', 'Goto', 'Extras', 'System', 'Help'];

        // Find menu index
        const topMenu = menuPath[0];
        const menuIndex = menuNames.indexOf(topMenu);

        if (menuIndex === -1) {
            console.warn('[SapMenu] Unknown top menu:', topMenu);
            return false;
        }

        // Click menu bar item
        const menuButton = this.frame.locator(`#wnd\\[0\\]\\/mbar\\/menu\\[${menuIndex}\\]`).first();

        if (await menuButton.isVisible({ timeout: 1000 })) {
            await menuButton.click({ force: true });
            await this.page.waitForTimeout(500);
            console.log(`[SapMenu] Opened: ${topMenu}`);
        } else {
            console.warn('[SapMenu] Menu button not visible');
            return false;
        }

        // Navigate submenus using keyboard
        for (let i = 1; i < menuPath.length; i++) {
            await this.page.waitForTimeout(300);
            await this.page.keyboard.press('ArrowDown');
        }

        // Select item
        await this.page.keyboard.press('Enter');
        await this.page.waitForTimeout(1000);

        console.log('[SapMenu] ✓ Menu navigation complete');
        return true;
    }

    /**
     * Right-click an element (use sparingly - unreliable)
     * @param {import('playwright').Locator} element - Element to right-click
     * @param {string} menuItemText - Text of menu item to select
     */
    async contextMenu(element, menuItemText) {
        console.log('[SapMenu] Right-clicking element for context menu');
        console.warn('[SapMenu] ⚠️  Context menus are unreliable - prefer shortcuts or toolbar');

        try {
            // Right-click
            await element.click({ button: 'right', force: true });
            await this.page.waitForTimeout(800);

            // Look for context menu items
            const menuItem = this.frame.locator('.urCMItem, .urMnuItem')
                .filter({ hasText: menuItemText })
                .first();

            if (await menuItem.isVisible({ timeout: 1000 })) {
                await menuItem.click({ force: true });
                await this.page.waitForTimeout(1000);
                console.log('[SapMenu] ✓ Context menu item clicked');
                return true;
            }

            console.warn('[SapMenu] Context menu item not found');
            return false;

        } catch (error) {
            console.error('[SapMenu] Context menu failed:', error.message);
            return false;
        }
    }

    /**
     * Open context menu using keyboard (Shift+F10)
     * More reliable than right-click
     */
    async contextMenuKeyboard() {
        console.log('[SapMenu] Opening context menu via keyboard');

        await this.page.keyboard.press('Shift+F10');
        await this.page.waitForTimeout(800);

        console.log('[SapMenu] ✓ Context menu opened');
    }

    /**
     * Navigate context menu using arrows and select
     * @param {number} downCount - Number of times to press ArrowDown
     */
    async selectFromContextMenu(downCount = 1) {
        console.log(`[SapMenu] Navigating context menu: ${downCount} down`);

        for (let i = 0; i < downCount; i++) {
            await this.page.keyboard.press('ArrowDown');
            await this.page.waitForTimeout(200);
        }

        await this.page.keyboard.press('Enter');
        await this.page.waitForTimeout(1000);

        console.log('[SapMenu] ✓ Context menu item selected');
    }

    /**
     * Get list of common shortcuts
     */
    getShortcuts() {
        return { ...this.shortcuts };
    }

    /**
     * Add or override a shortcut
     * @param {string} name - Shortcut name
     * @param {string} key - Key combination
     */
    addShortcut(name, key) {
        console.log(`[SapMenu] Adding shortcut: ${name} = ${key}`);
        this.shortcuts[name] = key;
    }

    /**
     * Send custom key sequence
     * @param {string} keys - Key or key combination
     * @param {number} waitAfter - Wait time after
     */
    async pressKey(keys, waitAfter = 500) {
        console.log(`[SapMenu] Pressing: ${keys}`);
        await this.page.keyboard.press(keys);
        await this.page.waitForTimeout(waitAfter);
    }

    /**
     * Type text (useful for command field)
     * @param {string} text - Text to type
     */
    async type(text) {
        console.log(`[SapMenu] Typing: ${text}`);
        await this.page.keyboard.type(text);
        await this.page.waitForTimeout(300);
    }

    /**
     * Press Enter
     */
    async enter() {
        await this.page.keyboard.press('Enter');
        await this.page.waitForTimeout(500);
    }

    /**
     * Press Escape
     */
    async escape() {
        await this.page.keyboard.press('Escape');
        await this.page.waitForTimeout(500);
    }

    /**
     * Press Tab
     */
    async tab() {
        await this.page.keyboard.press('Tab');
        await this.page.waitForTimeout(200);
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapMenu]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapMenu;
