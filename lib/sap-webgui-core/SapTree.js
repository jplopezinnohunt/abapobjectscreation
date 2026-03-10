/**
 * SapTree.js
 * Generic tree navigation for SAP WebGUI
 *
 * Based on 103 experimental scripts - key findings:
 * - Text-based locators MORE reliable than IDs
 * - Keyboard navigation MORE reliable than mouse clicks
 * - Right-click context menus are UNRELIABLE (avoid)
 * - Double-click or ArrowRight for expansion
 *
 * Handles:
 * - Tree node navigation by path
 * - Node expansion/collapse
 * - Node selection
 * - Keyboard-based traversal
 */

class SapTree {
    constructor(frame, page) {
        this.frame = frame;
        this.page = page;
    }

    /**
     * Select a tree node by navigating through a path
     * @param {string[]} path - Array of node names (e.g., ['Project', 'Data Model', 'Entity Types'])
     * @param {object} options - Navigation options
     * @returns {Promise<void>}
     */
    async selectNode(path, options = {}) {
        const {
            expandLast = false,
            timeout = 1000
        } = options;

        console.log('[SapTree] Selecting node path:', path.join(' → '));

        for (let i = 0; i < path.length; i++) {
            const nodeName = path[i];
            const isLast = i === path.length - 1;

            console.log(`[SapTree]   [${i + 1}/${path.length}] ${nodeName}`);

            // Find and click the node
            const node = await this._findNodeByText(nodeName);

            if (!node) {
                throw new Error(`Node not found: ${nodeName}`);
            }

            // Click to select
            await node.click({ force: true });
            await this.page.waitForTimeout(timeout);

            // Expand if not last node, or if explicitly requested
            if (!isLast || expandLast) {
                await this._expandNode(node);
                await this.page.waitForTimeout(timeout);
            }
        }

        console.log('[SapTree] ✓ Node selected:', path[path.length - 1]);
    }

    /**
     * Expand a specific node by path
     * @param {string[]} path - Node path to expand
     */
    async expandNode(path) {
        console.log('[SapTree] Expanding node:', path.join(' → '));
        await this.selectNode(path, { expandLast: true });
    }

    /**
     * Navigate tree using keyboard (most reliable method)
     * @param {string[]} directions - Array of keyboard directions
     * Example: ['ArrowDown', 'ArrowDown', 'ArrowRight', 'ArrowDown']
     */
    async navigateByKeyboard(directions) {
        console.log('[SapTree] Keyboard navigation:', directions.join(' → '));

        for (const direction of directions) {
            await this.page.keyboard.press(direction);
            await this.page.waitForTimeout(300);
        }

        console.log('[SapTree] ✓ Keyboard navigation complete');
    }

    /**
     * Check if a node is expanded
     * @param {string} nodeName - Node name to check
     * @returns {Promise<boolean>}
     */
    async isNodeExpanded(nodeName) {
        const node = await this._findNodeByText(nodeName);

        if (!node) {
            return false;
        }

        try {
            // Look for expand/collapse icon near the node
            const row = this.frame.locator('tr').filter({ has: node }).first();
            const expandIcon = row.locator('[title="Expand Node"]').first();

            // If "Expand Node" icon exists, node is collapsed
            if (await expandIcon.isVisible({ timeout: 500 })) {
                return false;
            }

            // Look for "Node expanded" or collapse icon
            const collapseIcon = row.locator('[title*="expanded"], [title="Collapse Node"]').first();
            if (await collapseIcon.isVisible({ timeout: 500 })) {
                return true;
            }

            // Fallback: assume expanded if children are visible
            return true;

        } catch (error) {
            console.warn('[SapTree] Could not determine expansion state:', error.message);
            return false;
        }
    }

    /**
     * Get currently selected/active node text
     */
    async getActiveNode() {
        try {
            const activeNodeText = await this.frame.evaluate(() => {
                const active = document.activeElement;
                return active ? active.innerText || active.textContent : null;
            });

            return activeNodeText ? activeNodeText.trim() : null;
        } catch (error) {
            console.warn('[SapTree] Could not get active node:', error.message);
            return null;
        }
    }

    /**
     * Double-click a node (alternative to expand)
     * @param {string} nodeName - Node name to double-click
     */
    async doubleClickNode(nodeName) {
        console.log('[SapTree] Double-clicking node:', nodeName);

        const node = await this._findNodeByText(nodeName);

        if (!node) {
            throw new Error(`Node not found: ${nodeName}`);
        }

        await node.dblclick({ force: true });
        await this.page.waitForTimeout(1500);

        console.log('[SapTree] ✓ Double-click complete');
    }

    /**
     * Find a tree node by text (uses multiple strategies)
     * @private
     */
    async _findNodeByText(text) {
        const strategies = [
            // Strategy 1: Exact text match on span/td
            () => this.frame.locator('span, td')
                .filter({ hasText: new RegExp(`^${this._escapeRegex(text)}$`) })
                .first(),

            // Strategy 2: Title attribute match
            () => this.frame.locator(`[title="${text}"]`).first(),

            // Strategy 3: Partial text match (looser)
            () => this.frame.locator('span, td')
                .filter({ hasText: text })
                .first(),

            // Strategy 4: Look in tree-specific elements
            () => this.frame.locator('.urTreeItem, .lsTextView')
                .filter({ hasText: text })
                .first()
        ];

        for (let i = 0; i < strategies.length; i++) {
            try {
                const node = strategies[i]();
                if (await node.isVisible({ timeout: 1000 })) {
                    console.log(`[SapTree]   ✓ Found using strategy ${i + 1}`);
                    return node;
                }
            } catch (error) {
                // Try next strategy
            }
        }

        console.warn(`[SapTree]   ✗ Node not found: ${text}`);
        return null;
    }

    /**
     * Expand a node (multiple strategies)
     * @private
     */
    async _expandNode(node) {
        try {
            // Strategy 1: Find and click expand icon
            const row = this.frame.locator('tr').filter({ has: node }).first();
            const expandIcon = row.locator('[title="Expand Node"], .urSTExpClo').first();

            if (await expandIcon.isVisible({ timeout: 500 })) {
                console.log('[SapTree]     → Clicking expand icon');
                await expandIcon.click({ force: true });
                return;
            }
        } catch (error) {
            // Expand icon not found, try keyboard
        }

        // Strategy 2: Use keyboard (most reliable)
        console.log('[SapTree]     → Using keyboard (ArrowRight)');
        await node.click({ force: true }); // Ensure focus
        await this.page.keyboard.press('ArrowRight');
    }

    /**
     * Collapse a node
     * @param {string} nodeName - Node name to collapse
     */
    async collapseNode(nodeName) {
        console.log('[SapTree] Collapsing node:', nodeName);

        const node = await this._findNodeByText(nodeName);

        if (!node) {
            throw new Error(`Node not found: ${nodeName}`);
        }

        await node.click({ force: true });
        await this.page.keyboard.press('ArrowLeft');
        await this.page.waitForTimeout(500);

        console.log('[SapTree] ✓ Node collapsed');
    }

    /**
     * Reset tree focus to root
     */
    async focusRoot() {
        console.log('[SapTree] Resetting to tree root');

        // Click first tree element
        const rootTree = this.frame.locator('[id^="tree#"]').first();
        await rootTree.click({ force: true });

        // Press Home to go to top
        await this.page.keyboard.press('Home');
        await this.page.waitForTimeout(500);

        console.log('[SapTree] ✓ At root');
    }

    /**
     * Escape regex special characters
     * @private
     */
    _escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Log helper
     */
    log(message, level = 'info') {
        const prefix = '[SapTree]';
        if (level === 'error') {
            console.error(prefix, message);
        } else if (level === 'warn') {
            console.warn(prefix, message);
        } else {
            console.log(prefix, message);
        }
    }
}

module.exports = SapTree;
