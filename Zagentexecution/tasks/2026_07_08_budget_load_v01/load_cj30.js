// CJ30 original-budget loader (V01 WebGUI). Fill all cells, single Enter, optional Save.
// Usage: node load_cj30.js <PROJECT> <YEAR> <commit|test> <WBS=AMT> ...
const G = require('../2026_06_25_staff_time_distribution_bcm/sap_gui_lib');
const PROJ=process.argv[2], YEAR=process.argv[3], MODE=process.argv[4];
const PLAN=process.argv.slice(5).map(s=>{const[w,a]=s.split('=');return{wbs:w,amt:a};});
setTimeout(()=>{console.error('HARD TIMEOUT');process.exit(9);},90000); // self-guard

const status=async p=>{const f=await G.frame(p);return f.evaluate(()=>{const s=document.querySelector('.urStatusbar,#stbar-msg-txt');return s?s.innerText.trim():'';});};
const tableId=async p=>{const f=await G.frame(p);return f.evaluate(()=>{const c=document.querySelector('[id^="tbl"][id*="[1,3]"]');return c?c.id.match(/^(tbl\d+)/)[1]:null;});};
const rowOf=async(p,w)=>{const f=await G.frame(p);return f.evaluate(x=>{for(const c of document.querySelectorAll('[id^="tbl"]')){const m=c.id.match(/^tbl\d+\[(\d+),(\d+)\]$/);if(m&&(c.innerText||'').trim()===x)return +m[1];}return -1;},w);};

(async()=>{
  const {page}=await G.connect();
  await G.tcode(page,'CJ30');
  let f=await G.frame(page);
  await f.locator('input[title="Project definition"]').fill(PROJ);
  const yr=f.locator('input[title="Year / Overall Value"]');
  if(await yr.count()) await yr.fill(YEAR);
  await page.keyboard.press('Enter'); await G.idle(page); await page.waitForTimeout(1500);

  const tbl=await tableId(page);
  for(const {wbs,amt} of PLAN){
    const row=await rowOf(page,wbs);
    if(row<0){console.log('SKIP '+wbs+' (row not found)');continue;}
    f=await G.frame(page);
    const cell=f.locator('[id="'+tbl+'['+row+',4]_c"]').first();
    await cell.click({clickCount:3}); await page.waitForTimeout(200);
    await page.keyboard.type(String(amt)); await page.waitForTimeout(200);
    console.log('TYPED '+wbs+'='+amt+' (row '+row+')');
  }
  await page.keyboard.press('Enter'); await G.idle(page); await page.waitForTimeout(1200);
  const st=await status(page); console.log('STATUS after validate: '+(st||'(none)'));
  if(/exceed|error|not allowed|greater|invalid/i.test(st)){console.log('!! ERROR — not saving');process.exit(3);}
  if(MODE!=='commit'){console.log('TEST — not saved');process.exit(0);}
  f=await G.frame(page);
  const save=f.locator('div[title^="Save"],[title="Save (Ctrl+S)"]').first();
  if(await save.count()) await save.click(); else await page.keyboard.press('Control+s');
  await G.idle(page); await page.waitForTimeout(1800);
  console.log('SAVE status: '+(await status(page)||'(none)'));
  process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
