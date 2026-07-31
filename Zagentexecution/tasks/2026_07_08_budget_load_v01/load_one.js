// One WBS budget per full CJ30 cycle (robust: no multi-row grid sync). 
// Usage: node load_one.js <PROJECT> <YEAR> <WBS> <AMT> <commit|test>
const G=require('../2026_06_25_staff_time_distribution_bcm/sap_gui_lib');
const [PROJ,YEAR,WBS,AMT,MODE]=process.argv.slice(2);
setTimeout(()=>{console.error('HARD TIMEOUT');process.exit(9);},70000);
const status=async p=>{const f=await G.frame(p);return f.evaluate(()=>{const s=document.querySelector('.urStatusbar,#stbar-msg-txt');return s?s.innerText.trim():'';});};
(async()=>{
  const {page}=await G.connect();
  await G.tcode(page,'CJ30');
  let f=await G.frame(page);
  await f.locator('input[title="Project definition"]').fill(PROJ);
  const yr=f.locator('input[title="Year / Overall Value"]'); if(await yr.count()) await yr.fill(YEAR);
  await page.keyboard.press('Enter'); await G.idle(page); await page.waitForTimeout(1500);
  // find row of WBS (fresh, before any edit), column-agnostic
  f=await G.frame(page);
  const loc=await f.evaluate(w=>{for(const c of document.querySelectorAll('[id^="tbl"]')){const m=c.id.match(/^(tbl\d+)\[(\d+),\d+\]$/);if(m&&(c.innerText||'').trim()===w)return{tbl:m[1],row:+m[2]};}return null;},WBS);
  if(!loc){console.log('WBS '+WBS+' not visible in grid');process.exit(2);}
  const cell=f.locator('[id="'+loc.tbl+'['+loc.row+',4]_c"]').first();
  await cell.click({clickCount:3}); await page.waitForTimeout(250);
  await page.keyboard.type(String(AMT)); await page.keyboard.press('Enter');
  await G.idle(page); await page.waitForTimeout(1200);
  const st=await status(page); console.log(WBS+'='+AMT+' | status: '+(st||'(none)'));
  if(/exceed|error|not allowed|greater|invalid/i.test(st)){console.log('!! ERROR — not saving');process.exit(3);}
  if(MODE!=='commit'){console.log('TEST — not saved');process.exit(0);}
  f=await G.frame(page);
  const save=f.locator('div[title^="Save"],[title="Save (Ctrl+S)"]').first();
  if(await save.count()) await save.click(); else await page.keyboard.press('Control+s');
  await G.idle(page); await page.waitForTimeout(1800);
  console.log('SAVE status: '+(await status(page)||'(none)'));
  process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
