// Run against a started local server with Playwright installed: node tests/studio_smoke.cjs
const { chromium } = require('playwright');
(async () => {
  const options = {headless: true, args: ['--autoplay-policy=no-user-gesture-required']};
  if (process.env.CHROME_PATH) options.executablePath = process.env.CHROME_PATH;
  const browser = await chromium.launch(options);
  const page = await browser.newPage({viewport: {width: 1280, height: 900}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  try {
    await page.goto(process.env.SOUNDSCAPE_TEST_URL || 'http://127.0.0.1:8765/', {waitUntil:'networkidle'});
    await page.getByRole('button', {name:'Try the sample'}).click();
    await page.waitForFunction(() => document.querySelector('#detectedScene').textContent.toLowerCase()==='forest');
    await page.locator('#quickRain').click();
    await page.waitForFunction(() => document.querySelector('#audioPrompt').value.includes('rain falling'));
    await page.locator('#generateBtn').click();
    await page.waitForFunction(() => document.querySelector('#previewPlay').getAttribute('aria-pressed')==='true');
    const playing=await page.evaluate(async()=>{const before=context.currentTime;await new Promise(r=>setTimeout(r,300));return context.state==='running'&&context.currentTime>before;});
    if(!playing||errors.length)throw new Error(JSON.stringify({playing,errors}));
    console.log('Forest, user-selected rain, prompt and live preview passed.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exit(1);});
