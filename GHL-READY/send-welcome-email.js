const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CHROME_USER_DATA = 'C:\\Users\\danga\\AppData\\Local\\Google\\Chrome\\User Data';
const PROFILE = 'Profile 2'; // Lilly's profile — logged into admin@dodealswithlee.com / lilly@dodealswithlee.com

const WELCOME_HTML = fs.readFileSync(
  path.join(__dirname, 'FINAL', 'welcome-pack-lilly.html'),
  'utf8'
);

const SIG_HTML = fs.readFileSync(
  path.join(__dirname, 'email-signatures', 'sig-admin.htm'),
  'utf8'
);

(async () => {
  console.log('[1/6] Launching Chrome with Lilly profile...');
  
  const context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    headless: false,
    channel: 'chrome',
    args: [
      `--profile-directory=${PROFILE}`,
      '--no-first-run',
      '--disable-blink-features=AutomationControlled'
    ],
    viewport: { width: 1400, height: 950 },
    timeout: 60000
  });

  const page = context.pages()[0] || await context.newPage();

  try {
    // Step 1: Go to Gmail
    console.log('[2/6] Opening Gmail...');
    await page.goto('https://mail.google.com/mail/u/0/#inbox', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    await page.waitForTimeout(4000);
    console.log('Gmail loaded. Current URL:', page.url());

    // Step 2: Click Compose
    console.log('[3/6] Clicking Compose...');
    // Try multiple selectors for the Compose button
    const composeSelectors = [
      'div.T-I.T-I-KE.L3',           // Gmail compose button class
      '[gh="cm"]',                      // Gmail compose attribute
      'div[role="button"]:has-text("Compose")',
      'text=Compose'
    ];
    
    let composed = false;
    for (const sel of composeSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn) {
          await btn.click();
          composed = true;
          console.log('  Compose clicked via:', sel);
          break;
        }
      } catch(e) { /* try next */ }
    }
    
    if (!composed) {
      // Fallback: keyboard shortcut
      console.log('  Using keyboard shortcut c...');
      await page.keyboard.press('c');
    }
    await page.waitForTimeout(2500);

    // Step 3: Fill To field
    console.log('[4/6] Filling email fields...');
    const toField = await page.$('input[aria-label="To recipients"], input[name="to"], textarea[aria-label="To recipients"]');
    if (toField) {
      await toField.click();
      await toField.fill('lilly@dodealswithlee.com');
      await page.keyboard.press('Tab');
      await page.waitForTimeout(500);
      console.log('  To: lilly@dodealswithlee.com');
    } else {
      console.log('  WARNING: Could not find To field');
    }

    // Step 4: Add CC
    // Click CC button first
    try {
      const ccLink = await page.$('span[aria-label="Add Cc recipients"], span:has-text("Cc")');
      if (ccLink) {
        await ccLink.click();
        await page.waitForTimeout(500);
      }
    } catch(e) {}
    
    const ccField = await page.$('input[aria-label="Cc recipients"], input[name="cc"]');
    if (ccField) {
      await ccField.click();
      await ccField.fill('daniel@exposuresolutions.me');
      await page.keyboard.press('Tab');
      await page.waitForTimeout(500);
      console.log('  CC: daniel@exposuresolutions.me');
    } else {
      console.log('  WARNING: Could not find CC field - will add manually');
    }

    // Step 5: Subject
    const subjectField = await page.$('input[name="subjectbox"], input[aria-label="Subject"]');
    if (subjectField) {
      await subjectField.click();
      await subjectField.fill('Welcome to Do Deals With Lee - Your Onboarding Pack');
      await page.waitForTimeout(300);
      console.log('  Subject set');
    }

    // Step 6: Body - paste the welcome pack HTML
    console.log('[5/6] Inserting welcome pack content...');
    const bodyField = await page.$('div[aria-label="Message Body"], div[role="textbox"]');
    if (bodyField) {
      await bodyField.click();
      
      // Insert the welcome HTML + signature via JS
      await page.evaluate((welcomeHtml, sigHtml) => {
        const body = document.querySelector('div[aria-label="Message Body"], div[role="textbox"]');
        if (body) {
          body.innerHTML = welcomeHtml + '<br/><br/>' + sigHtml;
          body.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, WELCOME_HTML, SIG_HTML);
      
      console.log('  Welcome pack HTML inserted with signature');
      await page.waitForTimeout(1000);
    } else {
      console.log('  WARNING: Could not find message body');
    }

    console.log('[6/6] Email composed! Review it in the browser window.');
    console.log('');
    console.log('=== READY TO SEND ===');
    console.log('To: lilly@dodealswithlee.com');
    console.log('CC: daniel@exposuresolutions.me');
    console.log('Subject: Welcome to Do Deals With Lee - Your Onboarding Pack');
    console.log('');
    console.log('The email is composed and waiting in Gmail.');
    console.log('Review it and click Send manually, or press Ctrl+Enter.');
    console.log('');
    console.log('Keeping browser open for 5 minutes for review...');
    
    // Keep open for review - don't auto-send
    await page.waitForTimeout(300000); // 5 minutes

  } catch (err) {
    console.error('Error:', err.message);
    console.log('');
    console.log('Browser is still open - you can complete the steps manually if needed.');
    await page.waitForTimeout(300000);
  }

  await context.close();
})();
