/**
 * launch_chrome_sap.js
 * Launches Chrome with remote debugging on port 9222 pointing to SAP D01/350
 * Run: node launch_chrome_sap.js
 * Keep this running in background, then use other scripts via CDP.
 */
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const SAP_URL = 'https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350';
const PROFILE_DIR = path.join(__dirname, 'playwright_data');

if (!fs.existsSync(PROFILE_DIR)) fs.mkdirSync(PROFILE_DIR, { recursive: true });

// Find Chrome path
const chromePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
];
const chrome = chromePaths.find(p => fs.existsSync(p));
if (!chrome) { console.error('Chrome not found'); process.exit(1); }

console.log(`Launching Chrome from: ${chrome}`);
console.log(`Profile dir: ${PROFILE_DIR}`);
console.log(`Remote debugging port: 9222`);
console.log(`Opening: ${SAP_URL}`);

const proc = spawn(chrome, [
    `--user-data-dir=${PROFILE_DIR}`,
    '--remote-debugging-port=9222',
    '--remote-allow-origins=*',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions-except=',
    SAP_URL
], { detached: true, stdio: 'ignore' });

proc.unref();
console.log(`Chrome launched with PID ${proc.pid}. Wait 3 seconds then run se24_write_methods.js`);
