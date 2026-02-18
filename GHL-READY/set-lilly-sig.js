const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CHROME_USER_DATA = 'C:\\Users\\danga\\AppData\\Local\\Google\\Chrome\\User Data';
const PROFILE = 'Profile 2'; // Lilly's profile

const SIG_HTML = fs.readFileSync(
  path.join(__dirname, 'email-signatures', 'sig-lilly.htm'),
  'utf8'
);

(async () => {
  console.log('Launching Chrome with Lilly profile...');
  
  const context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    headless: false,
    channel: 'chrome',
    args: [
      `--profile-directory=${PROFILE}`,
      '--no-first-run',
      '--disable-blink-features=AutomationControlled'
    ],
    viewport: { width: 1280, height: 900 }
  });

  const page = context.pages()[0] || await context.newPage();

  try {
    // Step 1: Go to Gmail settings signature page
    console.log('Opening Gmail settings...');
    await page.goto('https://mail.google.com/mail/u/0/#settings/general', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait for settings to load
    await page.waitForTimeout(3000);
    console.log('Gmail settings loaded.');

    // Step 2: Look for signature section - scroll down to find it
    // Gmail settings page - find the signature editor
    // First check if there's a "Create new" button for signatures
    const createNewBtn = await page.$('text=Create new');
    
    if (createNewBtn) {
      console.log('Found "Create new" signature button, clicking...');
      await createNewBtn.click();
      await page.waitForTimeout(1500);
      
      // Name the signature
      const nameInput = await page.$('input[aria-label="Name new signature"]');
      if (nameInput) {
        await nameInput.fill('Lilly - DDWL');
        // Click create/OK
        const okBtn = await page.$('button:has-text("Create")');
        if (okBtn) await okBtn.click();
        await page.waitForTimeout(1000);
      }
    }

    // Find the signature editor (contenteditable div inside the signature section)
    // Gmail uses an iframe or contenteditable for the signature editor
    console.log('Looking for signature editor...');
    
    // Try to find the signature contenteditable area
    const sigEditor = await page.$('div[aria-label="Signature text"] div[contenteditable="true"]');
    
    if (sigEditor) {
      console.log('Found signature editor, setting HTML...');
      // Clear existing content and paste new signature
      await sigEditor.click();
      await page.keyboard.press('Control+A');
      await page.keyboard.press('Delete');
      
      // Use clipboard to paste HTML
      await page.evaluate((html) => {
        const editor = document.querySelector('div[aria-label="Signature text"] div[contenteditable="true"]');
        if (editor) {
          editor.innerHTML = html;
          editor.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, SIG_HTML);
      
      console.log('Signature HTML set!');
      await page.waitForTimeout(1000);
      
      // Scroll down and click Save Changes
      console.log('Saving changes...');
      const saveBtn = await page.$('button:has-text("Save Changes")');
      if (saveBtn) {
        await saveBtn.scrollIntoViewIfNeeded();
        await saveBtn.click();
        await page.waitForTimeout(3000);
        console.log('Settings saved!');
      } else {
        console.log('Could not find Save Changes button - you may need to save manually.');
      }
    } else {
      console.log('Could not find signature editor automatically.');
      console.log('The Gmail settings page is open - you can set it manually.');
      console.log('Continuing to send test email...');
    }

    // Step 3: Compose and send test email
    console.log('Composing test email to daniel@exposuresolutions.me...');
    await page.goto('https://mail.google.com/mail/u/0/#inbox', { 
      waitUntil: 'networkidle',
      timeout: 20000 
    });
    await page.waitForTimeout(2000);

    // Click Compose
    const composeBtn = await page.$('div[gh="cm"]');
    if (composeBtn) {
      await composeBtn.click();
    } else {
      // Try alternate selector
      await page.click('text=Compose');
    }
    await page.waitForTimeout(2000);

    // Fill in To field
    const toField = await page.$('input[aria-label="To recipients"]');
    if (toField) {
      await toField.fill('daniel@exposuresolutions.me');
      await page.keyboard.press('Tab');
      await page.waitForTimeout(500);
    }

    // Fill in Subject
    const subjectField = await page.$('input[name="subjectbox"]');
    if (subjectField) {
      await subjectField.fill('Test Email - Lilly Signature Check');
      await page.waitForTimeout(500);
    }

    // Fill in body
    const bodyField = await page.$('div[aria-label="Message Body"]');
    if (bodyField) {
      await bodyField.click();
      await page.keyboard.type('Hi Daniel,\n\nThis is a test email to verify my new DDWL email signature is working correctly.\n\nPlease confirm you received this with the signature displayed properly.\n\nThanks,\nLilly');
      await page.waitForTimeout(500);
    }

    // Send the email
    console.log('Sending email...');
    const sendBtn = await page.$('div[aria-label="Send"]');
    if (sendBtn) {
      await sendBtn.click();
      console.log('Email sent!');
      await page.waitForTimeout(3000);
    } else {
      // Try keyboard shortcut
      await page.keyboard.press('Control+Enter');
      console.log('Email sent via keyboard shortcut!');
      await page.waitForTimeout(3000);
    }

    console.log('Done! Check daniel@exposuresolutions.me for the test email.');

  } catch (err) {
    console.error('Error:', err.message);
    console.log('Browser is still open - you can complete the steps manually.');
  }

  // Keep browser open for 10 seconds so user can see result
  await page.waitForTimeout(10000);
  await context.close();
})();
