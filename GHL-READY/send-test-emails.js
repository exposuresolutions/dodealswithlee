const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FINAL = path.join(__dirname, 'FINAL');
const CHROME_USER_DATA = 'C:\\Users\\danga\\AppData\\Local\\Google\\Chrome\\User Data';
const PROFILE = 'Profile 2';

async function sendEmail(page, to, subject, htmlFile) {
  const html = fs.readFileSync(path.join(FINAL, htmlFile), 'utf8');
  
  // Navigate to Gmail compose
  await page.goto('https://mail.google.com/mail/u/0/#inbox');
  await page.waitForTimeout(3000);
  
  // Click compose
  await page.click('div[gh="cm"]');
  await page.waitForTimeout(1500);
  
  // Fill To field
  await page.fill('input[name="to"]', to);
  await page.waitForTimeout(500);
  
  // Fill Subject
  await page.fill('input[name="subjectbox"]', subject);
  await page.waitForTimeout(500);
  
  // Click the body area and paste HTML
  const bodyDiv = page.locator('div[aria-label="Message Body"]');
  await bodyDiv.click();
  await page.waitForTimeout(300);
  
  // Use clipboard to paste HTML content
  await page.evaluate((htmlContent) => {
    const body = document.querySelector('div[aria-label="Message Body"]');
    if (body) {
      body.innerHTML = htmlContent;
      body.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }, html);
  
  await page.waitForTimeout(1000);
  console.log(`✅ Email composed: "${subject}" to ${to}`);
  console.log('   ⚠️  Review and click Send manually');
}

(async () => {
  console.log('🚀 Launching Chrome with Lilly profile...');
  
  const browser = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    channel: 'chrome',
    headless: false,
    args: [
      `--profile-directory=${PROFILE}`,
      '--no-first-run',
      '--disable-blink-features=AutomationControlled'
    ],
    viewport: { width: 1400, height: 900 },
    timeout: 30000
  });

  const page = await browser.newPage();
  
  try {
    // Email 1: Stacy Account Details (test to Daniel)
    await sendEmail(
      page,
      'daniel@exposuresolutions.me',
      '[TEST] Stacy Account Details & Onboarding - For Lee & Krystle Sign-Off',
      'email-stacy-account.html'
    );
    
    console.log('\n📧 First email composed. Opening second compose...');
    await page.waitForTimeout(2000);
    
    // Open new tab for second email
    const page2 = await browser.newPage();
    
    // Email 2: Site Review
    await sendEmail(
      page2,
      'daniel@exposuresolutions.me',
      '[TEST] DDWL Website Review - All Pages Live + New Features',
      'site-review-email.html'
    );
    
    console.log('\n✅ Both emails composed and ready for review!');
    console.log('👉 Review both tabs and click Send on each one.');
    console.log('   Press Ctrl+C when done.');
    
    // Keep browser open
    await new Promise(() => {});
    
  } catch (err) {
    console.error('Error:', err.message);
    // Keep browser open even on error
    await new Promise(() => {});
  }
})();
