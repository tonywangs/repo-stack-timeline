const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
  const context=await browser.newContext({offline:true});
  const page=await context.newPage();const errors=[],requests=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
  await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
  assert.match(await page.title(),/2019–2025/);
  assert.match(await page.locator('#coverage').innerText(),/4\/4 observed/);
  assert.equal(await page.locator('#sources tbody tr').count(),4);
  await page.selectOption('#ecosystem','python');
  await page.fill('#search','markupsafe');
  assert.equal(await page.locator('#prevalence tbody tr').count(),1);
  assert.deepEqual(await page.locator('#prevalence tbody tr td').allTextContents(),['1/2','1/2','1/3','1/3','1/4','1/4','2/4']);
  await page.selectOption('#mode','fixed');
  assert.deepEqual(await page.locator('#prevalence tbody tr td').allTextContents(),['1/2','1/2','1/2','1/2','1/2','1/2','2/2']);
  assert.match(await page.locator('#changes tbody').innerText(),/pallets\/flask/);
  await page.selectOption('#year','2019');
  assert.match(await page.locator('#change-title').innerText(),/baseline/);
  assert.equal(await page.locator('#sources tbody tr').filter({hasText:'unsupported_metadata'}).count(),2);
  await page.selectOption('#ecosystem','npm');await page.selectOption('#mode','available');
  await page.selectOption('#year','2021');await page.fill('#search','supports-color');
  assert.deepEqual(await page.locator('#changes tbody tr td').allTextContents(),['0/3','1/1','0/1','− chalk/chalk']);
  for(const href of await page.locator('#sources a').evaluateAll(as=>as.map(a=>a.href))){assert.match(href,/^https:\/\/github.com\/[^/]+\/[^/]+\/blob\/[0-9a-f]{40}\//)}
  await page.fill('#search','<script>window.bad=true</script>');
  assert.match(await page.locator('#prevalence tbody').innerText(),/No matching dependencies/);
  assert.equal(await page.evaluate(()=>window.bad),undefined);
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.fill('#search','');
  await page.locator('#search').focus();await page.keyboard.type('debug');
  assert.equal(await page.locator('#prevalence tbody tr').count(),1);
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  if(process.env.ANNUAL_SCREENSHOT)await page.screenshot({path:process.env.ANNUAL_SCREENSHOT,fullPage:true});
  console.log(JSON.stringify({status:'passed',checks:['offline local launch','year and ecosystem selectors','fixed-cohort prevalence','baseline','unknown coverage','removal risk denominator','exact source links','search and hostile text','390px viewport','keyboard input','no browser errors or network requests']}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
