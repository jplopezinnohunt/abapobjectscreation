# SAP WebGUI Core Framework

Generic, reusable automation primitives for SAP WebGUI built from 103+ experimental scripts.

## 🎯 Philosophy

**Generic Core → Specific Transactions**

- ✅ Core framework handles SAP WebGUI primitives (trees, toolbars, popups)
- ✅ Transaction modules use the core framework
- ✅ No hardcoded logic in core
- ✅ Complete separation of concerns

## 📦 Architecture

```
lib/
├── sap-webgui-core/          # Generic SAP WebGUI primitives
│   ├── SapConnection.js      # CDP connection, frame detection
│   ├── SapTree.js            # Tree navigation, expansion, selection
│   ├── SapToolbar.js         # Toolbar button interaction
│   ├── SapPopup.js           # Popup/dialog handling
│   ├── SapSession.js         # Session management, transport
│   ├── SapMenu.js            # Keyboard shortcuts, menus
│   └── index.js              # Exports all modules
│
└── sap-transactions/         # Transaction-specific implementations
    ├── SegwAutomation.js     # SEGW (Gateway Service Builder)
    ├── Se11Automation.js     # Data Dictionary (future)
    └── Se80Automation.js     # Object Navigator (future)
```

## 🔑 Key Design Patterns (From 103 Experiments)

### 1. Select-Then-Toolbar Pattern (Most Reliable)
**Finding:** Click tree node → Click toolbar button (not right-click menu)

```javascript
// ✅ GOOD - Uses proven pattern
await tree.selectNode(['Project', 'Data Model', 'Entity Types']);
await toolbar.clickCreate();

// ❌ BAD - Right-click menus are unreliable
await tree.rightClick(['Entity Types']);
await menu.selectContextMenuItem('Create');
```

### 2. Text-Based Locators > IDs
**Finding:** IDs change between sessions, text is more stable

```javascript
// ✅ GOOD
await tree.selectNode(['Data Model', 'Entity Types']);

// ❌ BAD
await frame.locator('#tree#C111#3#ni').click();
```

### 3. Keyboard > Mouse for Trees
**Finding:** Keyboard navigation is more predictable

```javascript
// ✅ GOOD
await node.click(); // Focus
await page.keyboard.press('ArrowRight'); // Expand

// ❌ BAD - Expand icon may not be clickable
await expandIcon.click();
```

### 4. Popups Always Use `.urPW`
**Finding:** Consistent across all SAP transactions

```javascript
const popup = frame.locator('.urPW').first();
await popup.waitFor({ state: 'visible' });
```

## 🚀 Quick Start

### Basic Usage

```javascript
const { SapConnection, SapTree, SapToolbar, SapPopup } = require('./lib/sap-webgui-core');

// Connect to existing SAP session
const conn = await SapConnection.connect();

// Create framework components
const tree = new SapTree(conn.frame, conn.page);
const toolbar = new SapToolbar(conn.frame, conn.page, 'C109');
const popup = new SapPopup(conn.frame, conn.page);

// Use them
await tree.selectNode(['Project', 'Data Model']);
await toolbar.clickButton(0); // Create button
await popup.fillFirst('EntityName');
await popup.confirm();
```

### Transaction-Specific Usage (SEGW Example)

```javascript
const { SapConnection } = require('./lib/sap-webgui-core');
const SegwAutomation = require('./lib/sap-transactions/SegwAutomation');

const conn = await SapConnection.connect();
const segw = new SegwAutomation(conn);

segw.setProject('Z_MY_SERVICE');

// Create entity - clean and simple!
await segw.createEntity('MyEntity', false);

// Add properties
await segw.addProperties('MyEntity', [
    { name: 'Id', type: 'Edm.String', key: true, maxLength: 10 },
    { name: 'Name', type: 'Edm.String', maxLength: 40 }
]);

await segw.save();
```

## 📚 Module Reference

### SapConnection
Handles CDP connection and frame management.

```javascript
const conn = await SapConnection.connect('http://localhost:9222', {
    transactionCode: 'SEGW',  // Optional: find specific transaction
    timeout: 10000,
    viewport: { width: 1920, height: 1080 }
});

await conn.waitForIdle();
await conn.navigateToTransaction('SE11');
const status = await conn.getStatusBarMessage();
await conn.screenshot('debug');
await conn.close();
```

### SapTree
Generic tree navigation.

```javascript
const tree = new SapTree(frame, page);

// Navigate by path (most common)
await tree.selectNode(['Project', 'Data Model', 'Entity Types']);

// Expand node
await tree.expandNode(['Data Model']);

// Keyboard navigation
await tree.navigateByKeyboard(['ArrowDown', 'ArrowDown', 'ArrowRight']);

// Check expansion state
const isExpanded = await tree.isNodeExpanded('Data Model');

// Double-click
await tree.doubleClickNode('Entity Types');

// Collapse
await tree.collapseNode('Data Model');
```

### SapToolbar
Context-sensitive toolbar buttons.

```javascript
const toolbar = new SapToolbar(frame, page, 'C109'); // Toolbar prefix

// Click by index (C109_btn0)
await toolbar.clickButton(0);

// Click by tooltip
await toolbar.clickButtonByTooltip('Create');

// Check state
const state = await toolbar.getButtonState(0); // 'enabled', 'disabled', 'active'

// Wait for button
await toolbar.waitForButtonEnabled(0, 5000);

// List all buttons (debugging)
const buttons = await toolbar.listButtons();

// Convenience methods
await toolbar.clickCreate(); // btn0
await toolbar.clickSave();   // Finds save button
```

### SapPopup
Generic popup/dialog handling.

```javascript
const popup = new SapPopup(frame, page);

// Wait and detect
await popup.waitForPopup(5000);
const title = await popup.getTitle();

// Fill by order
await popup.fillByOrder(['Value1', 'Value2']);

// Fill by label (more robust)
await popup.fill({
    'Entity Type Name': 'MyEntity',
    'Description': 'My Description'
});

// Fill first input (common case)
await popup.fillFirst('EntityName');

// Checkboxes
await popup.setCheckbox('Media', true);
await popup.setCheckbox('first', false); // First checkbox

// Confirm/Cancel
await popup.confirm();
await popup.cancel();

// All-in-one
await popup.handle('EntityName', {
    uncheckFirst: true,
    confirmMethod: 'keyboard'
});
```

### SapSession
Session and mode management.

```javascript
const session = new SapSession(frame, page, 'C109');

// Change mode
await session.ensureChangeMode();

// Transport handling
await session.handleTransportRequest(); // Auto-continue
await session.handleTransportRequest({ action: 'local' });
await session.handleTransportRequest({ action: 'specify', transportId: 'DEVK900123' });

// Save
await session.save(true); // Auto-handle transport

// Status bar
const status = await session.getStatusBarMessage();
await session.waitForStatus('generated', 10000);
const hasError = await session.hasError();
const hasSuccess = await session.hasSuccess();

// Navigation
await session.executeTransaction('SE11');
await session.goBack();   // F3
await session.exit();     // Shift+F3
await session.refresh();  // F8
```

### SapMenu
Keyboard shortcuts and menus.

```javascript
const menu = new SapMenu(frame, page);

// Shortcuts
await menu.shortcut('save');    // Ctrl+S
await menu.shortcut('create');  // F6
await menu.shortcut('F8');      // Direct key

// Menu bar (more reliable than context menu)
await menu.openMenuBar(['Edit', 'Create']);

// Context menu (use sparingly - unreliable)
await menu.contextMenuKeyboard();
await menu.selectFromContextMenu(2); // 2 down, then Enter

// Typing
await menu.type('Z_PROJECT');
await menu.enter();
await menu.escape();
await menu.tab();
```

## 🧪 Testing

Run the framework validation test:

```bash
# Prerequisites:
# 1. Chrome running: chrome.exe --remote-debugging-port=9222
# 2. SAP WebGUI logged in
# 3. SEGW transaction open with project Z_CRP_SRV

node test_framework.js
```

Expected output:
```
✓ Connected successfully
✓ Entity created
✓ Properties added
✓ Saved
✓✓✓ FRAMEWORK TEST PASSED ✓✓✓
```

## ✨ Benefits Over Previous Approach

### Before (segw_utils.js - 279 lines, mixed concerns)
```javascript
// Hardcoded for SEGW only
await this.navigateTree(['Z_CRP_SRV', 'Data Model', 'Entity Types']);
// Popup handling embedded
// Transport handling embedded
// 100+ lines per operation
```

### After (Framework - Clean separation)
```javascript
// Generic, reusable across all transactions
const tree = new SapTree(frame, page);
await tree.selectNode(['Z_CRP_SRV', 'Data Model', 'Entity Types']);

const toolbar = new SapToolbar(frame, page);
await toolbar.clickCreate();

const popup = new SapPopup(frame, page);
await popup.handle('EntityName');

// 10-20 lines per operation
```

## 📈 Success Metrics

- ✅ **< 20 lines** to create SEGW entity (vs 100+ before)
- ✅ **100% reusable** across SAP transactions
- ✅ **Zero transaction-specific logic** in core modules
- ✅ **Self-documenting** code with clear separation
- ✅ **Proven patterns** from 103 experiments

## 🔮 Future: Adding New Transactions

To automate a new transaction (e.g., SE11):

```javascript
// lib/sap-transactions/Se11Automation.js
const { SapTree, SapToolbar, SapPopup, SapSession } = require('../sap-webgui-core');

class Se11Automation {
    constructor(connection) {
        this.tree = new SapTree(connection.frame, connection.page);
        this.toolbar = new SapToolbar(connection.frame, connection.page, 'C110'); // SE11 prefix
        this.popup = new SapPopup(connection.frame, connection.page);
        this.session = new SapSession(connection.frame, connection.page);
    }

    async createTable(tableName) {
        // Use generic primitives - no need to reinvent tree navigation!
        await this.tree.selectNode(['Tables']);
        await this.toolbar.clickCreate();
        await this.popup.fillFirst(tableName);
        await this.popup.confirm();
    }
}
```

**That's it!** All the hard work (tree navigation, popup handling, etc.) is already done in the core framework.

## 📝 Key Learnings Preserved

1. **Never use browser_subagent** - Always CDP to port 9222
2. **Select-then-Toolbar is most reliable** - Don't fight context menus
3. **Keyboard > Mouse for trees** - More predictable
4. **Text locators > IDs** - More stable across sessions
5. **Transport handling is async** - Always check after saves
6. **Frame context matters** - Cache and reuse frame reference

## 🤝 Contributing

When adding new patterns or fixing issues:
1. Update the core module if it's a generic SAP WebGUI pattern
2. Update transaction module if it's specific to one transaction
3. Document in [.agents/rules/sapwebgui_framework_findings.md](../.agents/rules/sapwebgui_framework_findings.md)
4. Add test case in test_framework.js

---

Built with ❤️ from 103 experimental scripts and hard-earned findings.
