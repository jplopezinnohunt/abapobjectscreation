/**
 * SAP WebGUI Core Framework
 * Generic, reusable automation primitives for SAP WebGUI
 *
 * Based on 103+ experimental scripts and documented findings
 *
 * Usage:
 * ```javascript
 * const { SapConnection, SapTree, SapToolbar, SapPopup, SapSession, SapMenu } = require('./lib/sap-webgui-core');
 *
 * // Connect
 * const conn = await SapConnection.connect();
 *
 * // Create instances
 * const tree = new SapTree(conn.frame, conn.page);
 * const toolbar = new SapToolbar(conn.frame, conn.page, 'C109');
 * const popup = new SapPopup(conn.frame, conn.page);
 * const session = new SapSession(conn.frame, conn.page);
 * const menu = new SapMenu(conn.frame, conn.page);
 *
 * // Use them
 * await tree.selectNode(['Project', 'Data Model', 'Entity Types']);
 * await toolbar.clickCreate();
 * await popup.handle('EntityName');
 * ```
 */

const SapConnection = require('./SapConnection');
const SapTree = require('./SapTree');
const SapToolbar = require('./SapToolbar');
const SapPopup = require('./SapPopup');
const SapSession = require('./SapSession');
const SapMenu = require('./SapMenu');

module.exports = {
    SapConnection,
    SapTree,
    SapToolbar,
    SapPopup,
    SapSession,
    SapMenu
};
