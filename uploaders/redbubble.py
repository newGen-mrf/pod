"""
POD Automation Pipeline — Redbubble Uploader
Uses Playwright for safe browser automation.
Includes rate limiting, delays, and session management.
"""

import json
import logging
import os
import random
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import config

logger = logging.getLogger("pod.redbubble")

# Session storage for keeping logged in across runs
SESSION_FILE = os.path.join(config.OUTPUT_DIR, "rb_session.json")


def upload_to_redbubble(design_path: str, seo: dict, state: dict) -> dict:
    """
    Safely automate Redbubble upload using Playwright.
    Checks rate limits based on state history.
    """
    if not config.ENABLE_REDBUBBLE:
        logger.info("Redbubble disabled (no credentials) — skipping")
        return {"status": "skipped", "reason": "no credentials"}

    # Check safe limits today
    today = time.strftime("%Y-%m-%d")
    uploads_today = sum(
        1
        for u in state.get("uploaded", {}).get("redbubble", [])
        if u.get("date") == today
    )

    if uploads_today >= config.REDBUBBLE_MAX_UPLOADS_PER_RUN:
        logger.warning(f"Redbubble limit reached ({uploads_today} today) — skipping")
        return {"status": "skipped", "reason": "daily limit"}

    result = {"status": "failed"}

    # Use a random delay before starting to seem human
    random_delay = random.randint(10, 30)
    logger.info(f"Redbubble uploader sleeping {random_delay}s for safety...")
    time.sleep(random_delay)

    try:
        with sync_playwright() as p:
            # Mask as a real browser
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            # Load previous session if exists
            if os.path.exists(SESSION_FILE):
                try:
                    with open(SESSION_FILE, "r") as f:
                        cookies = json.load(f)
                    context.add_cookies(cookies)
                    logger.info("Loaded previous session cookies")
                except Exception as e:
                    logger.warning(f"Could not load session cookies: {e}")

            page = context.new_page()

            # Steganography bypass attempt for basic bot detection
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Step 1: Login (if needed)
            logged_in = _ensure_login(page, context)
            if not logged_in:
                raise RuntimeError("Failed to log in to Redbubble")

            # Step 2: Upload
            logger.info("Navigating to Add New Work page...")
            page.goto("https://www.redbubble.com/portfolio/images/new", timeout=60000)
            page.wait_for_load_state("networkidle")

            # Upload Image
            file_input = page.locator("input[type='file'][accept*='image']")
            file_input.set_input_files(design_path)
            logger.info("Image file selected")
            
            # Wait for upload to complete (spinner disappears)
            # This can take time depending on image size
            time.sleep(10) 

            # Fill Form
            _human_type(page, "#work_title_en", seo["title"])
            
            tags_str = ", ".join(seo["tags"][:15])
            _human_type(page, "#work_tag_field_en", tags_str)
            
            _human_type(page, "#work_description_en", seo["description"])

            # Enable all products (or select ones if logic added)
            # By default Redbubble enables most products automatically if image is large
            time.sleep(2)

            # Set Mature Content (No)
            page.click("#rightsDeclaration")
            page.check("#work_safe_true")

            # Step 3: Submit
            logger.info("Submitting design...")
            page.click("#submit-work")
            
            # Wait for success redirect
            page.wait_for_url("**/works/**", timeout=60000)
            logger.info("Upload Successful!")

            # Save updated cookies
            cookies = context.cookies()
            with open(SESSION_FILE, "w") as f:
                json.dump(cookies, f)

            result = {
                "status": "success",
                "date": today,
                "url": page.url,
            }

            browser.close()

    except Exception as e:
        logger.error(f"Redbubble upload failed: {e}")
        result["error"] = str(e)
        
    return result


def _ensure_login(page, context) -> bool:
    """Check if logged in, perform login if not. Return True if logged in."""
    page.goto("https://www.redbubble.com/explore/for-you", timeout=60000)
    page.wait_for_load_state("networkidle")

    # Check if login link exists (meaning we are NOT logged in)
    login_link = page.query_selector("a[href*='/auth/login']")
    
    if login_link:
        logger.info("Not logged in. Attempting login...")
        page.goto("https://www.redbubble.com/auth/login", timeout=60000)
        
        _human_type(page, "#ReduxFormInput1", config.REDBUBBLE_EMAIL)
        time.sleep(0.5)
        _human_type(page, "#ReduxFormInput2", config.REDBUBBLE_PASSWORD)
        time.sleep(1)
        
        # Click login button
        page.click("button[type='submit']")
        
        # Wait for navigation
        try:
            page.wait_for_url("**/explore/for-you**", timeout=15000)
            logger.info("Login successful.")
        except PlaywrightTimeout:
            # Check for Captcha
            if page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i]").count() > 0:
                logger.error("CAPTCHA detected on login. Cannot proceed autonomously.")
                return False
            logger.error("Login redirect timeout. Check credentials.")
            return False

    return True


def _human_type(page, selector: str, text: str):
    """Type text with random delays to simulate human typing."""
    page.click(selector)
    # Fast typing for bulk text, delay between 10ms and 50ms
    page.type(selector, text, delay=random.randint(10, 50))
    time.sleep(random.uniform(0.5, 1.5))
