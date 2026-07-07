const G = require('./sap_gui_lib');
(async () => {
    const { page } = await G.connect();
    await G.tcode(page, 'CJ30');
    await G.dump(page, 'CJ30 initial');
    await G.shot(page, 'cj30_initial');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
