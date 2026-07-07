const G = require('./sap_gui_lib');
(async () => {
    const { page } = await G.connect();
    await G.tcode(page, 'CJBV');
    await G.dump(page, 'CJBV selection screen');
    await G.shot(page, 'cjbv_initial');
    process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
