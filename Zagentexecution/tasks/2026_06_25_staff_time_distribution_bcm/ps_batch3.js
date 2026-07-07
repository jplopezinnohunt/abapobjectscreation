const G = require('./sap_gui_lib');
const AMT = '100000';
const ALL = ['CJ30','CJ32','CJBV'];
const TASKS = [ {p:'547RAF1001',steps:ALL},{p:'520RAF1015',steps:ALL},{p:'503RAF1003',steps:ALL},{p:'526RAS1036',steps:ALL},{p:'927CMR5001',steps:ALL},{p:'218BDI5000',steps:ALL},];const _OLD=[
    { p:'218BDI2000', steps:['CJ32','CJBV'] },   // CJ30 already done
    { p:'501UZB5002', steps:ALL }, { p:'728RAS2003', steps:ALL },
    { p:'547RAF1001', steps:ALL }, { p:'520RAF1015', steps:ALL },
    { p:'503RAF1003', steps:ALL }, { p:'526RAS1036', steps:ALL },
    { p:'927CMR5001', steps:ALL }, { p:'218BDI5000', steps:ALL },
];
async function status(page){const f=await G.frame(page);return await f.evaluate(()=>{const t=document.body.innerText.split('\n').map(s=>s.trim()).filter(Boolean);return t.find(s=>/posted|active|error|does not|exceeded/i.test(s))||'';}).catch(()=>'');}
async function entry(page,tc,proj){
    await G.tcode(page,tc); let f=await G.frame(page);
    await f.locator('input[title="Project definition"]').first().fill(proj);
    await page.keyboard.press('Enter'); await G.idle(page); await page.waitForTimeout(1200);
    f=await G.frame(page); const c=f.locator('input[id*="[1,4]_c"]').first();
    await c.click(); await c.fill(AMT); await page.keyboard.press('Enter');
    await G.idle(page); await page.waitForTimeout(900); f=await G.frame(page);
    const s=f.locator('div[title^="Save"], [title="Save (Ctrl+S)"]').first();
    if(await s.count())await s.click(); else await page.keyboard.press('Control+s');
    await G.idle(page); await page.waitForTimeout(1200); return await status(page);
}
async function cjbv(page,proj){await G.tcode(page,'CJBV');let f=await G.frame(page);
    await f.locator('input[title="Project definition"]').first().fill(proj);
    await page.keyboard.press('F8'); await G.idle(page); await page.waitForTimeout(1500); return await status(page);}
(async()=>{const{page}=await G.connect();
    for(const t of TASKS){const r={};
        for(const st of t.steps){ r[st]= st==='CJBV'?await cjbv(page,t.p):await entry(page,st,t.p); }
        console.log(`${t.p} ${JSON.stringify(r)}`);
    }
    console.log('BATCH DONE'); process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
