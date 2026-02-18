"""
GHL IVR Builder Agent — browser-use + GHL Workflow AI Builder
=============================================================
An AI agent that:
1. Opens GHL in Chrome (Profile 4 — already logged in)
2. Navigates to the Workflow AI Builder
3. Prompts GHL's own AI to create the IVR workflow
4. Reviews and customizes the result
5. Saves and publishes

Uses browser-use (AI-driven browser automation) instead of brittle Playwright selectors.
The agent SEES the screen and FIGURES OUT what to click.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Load env
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# GHL Config
GHL_LOCATION = "KbiucErIMNPbO1mY4qXL"
GHL_WORKFLOWS_URL = f"https://app.gohighlevel.com/location/{GHL_LOCATION}/automation/list"

# Chrome Profile 4 (admin@dodealswithlee.com — logged into GHL)
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
CHROME_PROFILE = "Profile 4"

# The detailed IVR prompt for GHL's Workflow AI Builder
IVR_PROMPT = """Build an IVR phone system workflow for phone number (813) 675-0916 with the following structure:

TRIGGER: Start IVR on inbound call to (813) 675-0916

STEP 1 - GREETING: Say/Play message: "Thank you for calling Do Deals with Lee. Tampa Bay's trusted real estate investment partner."

STEP 2 - MAIN MENU: Gather Input with this message: "Press 1 to sell your home to Lee. Press 2 for coaching and events. Press 3 to do a deal or fund a deal with Lee. Press 4 for operations and general inquiries. Press 0 to speak with a team member. Or stay on the line to leave a message."
Set loops to 2. Enable match conditions with these branches:

BRANCH 1 (Key 1 - Sell Home):
- Say message: "We buy homes fast. No repairs, no fees, no hassle. Let us connect you with our acquisitions team."
- Connect call to users: Krystle Gordon and Lee Kearney. Timeout 30 seconds. Enable call recording.
- If no answer: Record voicemail with message "Please leave your name, number, and property address. We'll get back to you within 24 hours."
- End call

BRANCH 2 (Key 2 - Coaching & Events):
- Say message: "Lee Kearney offers private one-on-one coaching and live real estate investing events."
- Gather input: "Press 1 for upcoming events. Press 2 for private coaching. Press 0 to go back to the main menu."
  - Sub-branch 1 (Events): Say "Visit dodealswithlee.com slash events for our next live event. Or leave a message and we'll send you the details." Then record voicemail, end call.
  - Sub-branch 2 (Coaching): Say "Our coaching program includes personalized portfolio analysis and action plans. Let me connect you with our team." Connect call to Krystle Gordon, timeout 30s, record voicemail on no answer, end call.

BRANCH 3 (Key 3 - Deals):
- Say message: "Partner with Lee Kearney on your next real estate deal."
- Gather input: "Press 1 to submit a deal. Press 2 to fund a deal with Lee. Press 0 to go back."
  - Sub-branch 1 (Submit Deal): Say "Visit dodealswithlee.com to submit your deal online, or leave your details after the tone." Record voicemail, end call.
  - Sub-branch 2 (Fund Deal): Say "Lee's lending program offers high-velocity wholesale and cosmetic rehab opportunities across Florida. Let me connect you with Lee." Connect call to Lee Kearney, timeout 30s, record voicemail on no answer, end call.

BRANCH 4 (Key 4 - Operations):
- Say message: "Connecting you with our operations team."
- Connect call to users: Krystle Gordon, Becky Williams, and Stacy Platt. Timeout 30 seconds.
- If no answer: Record voicemail with message "You've reached Do Deals with Lee operations. Please leave a message and we'll return your call."
- End call

BRANCH 0 (Key 0 - Team Member):
- Say message: "Please hold while we connect you."
- Connect call to ALL team members. Timeout 30 seconds.
- If no answer: Record voicemail, end call.

NO INPUT / DEFAULT:
- Say message: "We didn't receive your selection. Please leave a message after the tone."
- Record voicemail
- End call

Name this workflow: DDWL Main Line IVR"""


class AnthropicLLM:
    """Wrapper around Anthropic API that satisfies browser-use's BaseChatModel Protocol."""

    def __init__(self, model: str, api_key: str, max_tokens: int = 4096):
        self.model = model
        self._api_key = api_key
        self._max_tokens = max_tokens
        self._verified_api_keys = True
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def provider(self) -> str:
        return "anthropic"

    @property
    def name(self) -> str:
        return f"anthropic/{self.model}"

    @property
    def model_name(self) -> str:
        return self.model

    async def ainvoke(self, messages: list, output_format: Any = None, **kwargs) -> Any:
        """Call Anthropic API with browser-use message format."""
        from browser_use.llm.base import ChatInvokeCompletion

        # Convert browser-use messages to Anthropic format
        system_msg = ""
        anthropic_msgs = []
        for msg in messages:
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', '')

            if role == 'system':
                if isinstance(content, str):
                    system_msg = content
                elif isinstance(content, list):
                    system_msg = " ".join(
                        p.get('text', '') if isinstance(p, dict) else str(p)
                        for p in content
                    )
                continue

            # Handle content that may be a list of parts (text + images)
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get('type') == 'text':
                            parts.append({'type': 'text', 'text': part['text']})
                        elif part.get('type') == 'image_url':
                            url = part.get('image_url', {}).get('url', '')
                            if url.startswith('data:'):
                                # base64 image
                                media_type = url.split(';')[0].split(':')[1]
                                data = url.split(',')[1]
                                parts.append({
                                    'type': 'image',
                                    'source': {
                                        'type': 'base64',
                                        'media_type': media_type,
                                        'data': data,
                                    }
                                })
                    elif hasattr(part, 'type'):
                        if part.type == 'text':
                            parts.append({'type': 'text', 'text': part.text})
                        elif part.type == 'image_url':
                            url = part.image_url.url if hasattr(part.image_url, 'url') else part.image_url.get('url', '')
                            if url.startswith('data:'):
                                media_type = url.split(';')[0].split(':')[1]
                                data = url.split(',')[1]
                                parts.append({
                                    'type': 'image',
                                    'source': {
                                        'type': 'base64',
                                        'media_type': media_type,
                                        'data': data,
                                    }
                                })
                content = parts if parts else [{'type': 'text', 'text': str(content)}]
            elif isinstance(content, str):
                content = [{'type': 'text', 'text': content}]

            api_role = 'assistant' if role == 'assistant' else 'user'
            anthropic_msgs.append({'role': api_role, 'content': content})

        # Call Anthropic
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self._max_tokens,
                system=system_msg if system_msg else "You are a helpful browser automation agent.",
                messages=anthropic_msgs,
            )
            text = response.content[0].text if response.content else ""
            usage = response.usage

            from browser_use.llm.views import ChatInvokeUsage

            # Get cache tokens if available
            cached = getattr(usage, 'cache_read_input_tokens', 0) or 0
            cache_creation = getattr(usage, 'cache_creation_input_tokens', 0) or 0

            return ChatInvokeCompletion(
                completion=text,
                usage=ChatInvokeUsage(
                    prompt_tokens=usage.input_tokens,
                    prompt_cached_tokens=cached,
                    prompt_cache_creation_tokens=cache_creation,
                    prompt_image_tokens=0,
                    completion_tokens=usage.output_tokens,
                    total_tokens=usage.input_tokens + usage.output_tokens,
                ),
                stop_reason=response.stop_reason,
            )
        except Exception as e:
            print(f"  Anthropic API error: {e}")
            raise


async def run_agent():
    """Run the browser-use agent to create the IVR workflow in GHL."""
    from browser_use import Agent, Browser

    print("\n" + "=" * 60)
    print("  GHL IVR Builder Agent")
    print("  Using: browser-use + GHL Workflow AI Builder")
    print("=" * 60)

    # Set up the LLM (Claude — vision-capable for browser-use)
    llm = AnthropicLLM(
        model="claude-sonnet-4-20250514",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
    )

    # Use a lightweight dedicated profile dir (not Chrome's massive User Data)
    # First login will require manual auth, but session persists for future runs
    AGENT_PROFILE = str(Path(__file__).parent / "browser-profiles" / "ghl-agent")
    Path(AGENT_PROFILE).mkdir(parents=True, exist_ok=True)

    print(f"\n  Launching browser (lightweight profile at {AGENT_PROFILE})...")
    browser = Browser(
        user_data_dir=AGENT_PROFILE,
        keep_alive=True,
    )

    # Task 1: Navigate to GHL Workflows and use the AI Builder
    task1 = f"""You are automating GoHighLevel (GHL) CRM to build an IVR phone system workflow.

STEP 1: Navigate to {GHL_WORKFLOWS_URL}
- Wait for the page to fully load. You should see a list of workflows or a "Create Workflow" button.
- If you see a login page, wait — the user will log in manually.

STEP 2: Start the AI Workflow Builder
- Look for a button that says "Build using AI" or "+ Create Workflow" on the workflows list page.
- Click "Build using AI" if available. This opens a text prompt where you can describe the workflow.
- If "Build using AI" is not visible, click "+ Create Workflow" first, then look for an AI prompt box or AI chatbot icon in the workflow builder.

STEP 3: Enter the IVR prompt
- Once you see the AI prompt input (a text box or chat interface), paste or type this EXACT prompt:

{IVR_PROMPT}

STEP 4: Submit and wait
- Click "Build Workflow" or "Send" or whatever button submits the prompt.
- Wait for the AI to generate the workflow. This may take 10-30 seconds.
- Once generated, take note of what was created.

STEP 5: Review
- Look at the generated workflow structure.
- Report back what triggers, actions, and branches were created.
- Do NOT publish yet — just confirm the structure looks correct.

IMPORTANT: 
- Be patient with page loads — GHL can be slow.
- If a modal or popup appears, read it and handle appropriately.
- If the AI Builder asks clarifying questions, answer them based on the IVR prompt details above.
"""

    print("  Creating agent...")
    agent = Agent(
        task=task1,
        llm=llm,
        browser=browser,
        max_actions_per_step=5,
    )

    print("  Running agent — building IVR workflow via GHL AI Builder...")
    print("  (Watch the Chrome window — the agent is controlling it)\n")

    try:
        history = await agent.run(max_steps=30)
        print("\n  Agent completed Task 1!")
        print(f"  Steps taken: {len(history.history)}")

        # Task 2: Review and adjust if needed
        agent.add_new_task("""
Review the workflow that was just created:
1. Check if the trigger is set to phone number (813) 675-0916
2. Check if all 5 branches exist (keys 1-4 and 0)
3. Check if Connect Call actions have the correct team members assigned
4. If anything is missing or wrong, use the AI chatbot in the workflow builder to fix it
5. Report what you see — list all the actions and branches

Do NOT publish the workflow yet. Just report the current state.
""")

        print("\n  Running Task 2 — reviewing workflow...")
        history2 = await agent.run(max_steps=15)
        print(f"\n  Agent completed Task 2!")
        print(f"  Steps taken: {len(history2.history)}")

    except Exception as e:
        print(f"\n  ❌ Agent error: {e}")
        import traceback
        traceback.print_exc()

    print("\n  Browser stays open for manual review.")
    print("  Press Ctrl+C to exit.\n")

    try:
        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("  Closing browser...")
        await browser.kill()


if __name__ == "__main__":
    asyncio.run(run_agent())
