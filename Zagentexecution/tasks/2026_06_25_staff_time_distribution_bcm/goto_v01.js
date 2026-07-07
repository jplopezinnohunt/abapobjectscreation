const G = require('./sap_gui_lib');
(async () => {
    const { page } = await G.connect();
    await page.goto('https://hq-sap-v01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350',
                    { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(6000);
    console.log('TITLE:', await page.title());
    console.log('URL:', page.url());
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
