"""
POD Automation Pipeline — Trend Discovery Engine
Multi-source trend discovery with category awareness and deduplication.
"""

import json
import logging
import os
import random
import time

import config

logger = logging.getLogger("pod.trends")


def discover_trend(category: dict, state: dict) -> str:
    """
    Discover a trending topic relevant to the given category.
    Checks multiple sources and deduplicates against history.
    Returns a trend string suitable for design prompt generation.
    """
    logger.info(f"Discovering trends for category: {category['name']}")

    # Collect trends from multiple sources
    all_trends = []

    # Source 1: Etsy trending (highest signal for POD)
    try:
        etsy_trends = _scrape_etsy_trends(category)
        all_trends.extend([(t, 3) for t in etsy_trends])  # weight 3
        logger.info(f"Etsy: found {len(etsy_trends)} trends")
    except Exception as e:
        logger.warning(f"Etsy scraping failed: {e}")

    # Source 2: Pinterest
    try:
        pinterest_trends = _scrape_pinterest_trends(category)
        all_trends.extend([(t, 2) for t in pinterest_trends])  # weight 2
        logger.info(f"Pinterest: found {len(pinterest_trends)} trends")
    except Exception as e:
        logger.warning(f"Pinterest scraping failed: {e}")

    # Source 3: Reddit
    try:
        reddit_trends = _scrape_reddit_trends(category)
        all_trends.extend([(t, 1) for t in reddit_trends])  # weight 1
        logger.info(f"Reddit: found {len(reddit_trends)} trends")
    except Exception as e:
        logger.warning(f"Reddit scraping failed: {e}")

    # Deduplicate against history
    used_trends = set(t.lower() for t in state.get("trends_used", []))
    fresh_trends = [(t, w) for t, w in all_trends if t.lower() not in used_trends]

    if not fresh_trends:
        fresh_trends = all_trends  # Reset if all used

    if not fresh_trends:
        # Ultimate fallback: use category keywords + AI enhancement
        trend = _generate_ai_trend(category)
        logger.info(f"AI-generated fallback trend: {trend}")
        return trend

    # Weighted random selection
    trend = _weighted_choice(fresh_trends)
    logger.info(f"Selected trend: {trend}")
    return trend


def _scrape_etsy_trends(category: dict) -> list:
    """Scrape Etsy for trending search terms related to the category."""
    from playwright.sync_api import sync_playwright

    trends = []
    keywords = category.get("trend_keywords", [])
    if not keywords:
        keywords = [category["name"]]

    search_query = random.choice(keywords) + " shirt"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        try:
            page.goto(
                f"https://www.etsy.com/search?q={search_query.replace(' ', '+')}",
                timeout=15000,
            )
            page.wait_for_timeout(3000)

            # Extract listing titles
            titles = page.query_selector_all("h3.v2-listing-card__title")
            for t in titles:
                text = t.inner_text().strip()
                if len(text) > 10 and len(text) < 150:
                    trends.append(text)
        except Exception as e:
            logger.warning(f"Etsy page error: {e}")
        finally:
            browser.close()

    return trends[:15]


def _scrape_pinterest_trends(category: dict) -> list:
    """Scrape Pinterest for trending pin concepts."""
    from playwright.sync_api import sync_playwright

    trends = []
    keywords = category.get("trend_keywords", [])
    if not keywords:
        keywords = [category["name"]]

    search_query = random.choice(keywords) + " design"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        try:
            page.goto(
                f"https://www.pinterest.com/search/pins/?q={search_query.replace(' ', '%20')}",
                timeout=15000,
            )
            page.wait_for_timeout(5000)

            # Extract pin aria-labels
            pins = page.query_selector_all("a[aria-label][href*='/pin/']")
            for pin in pins:
                label = pin.get_attribute("aria-label")
                if label and len(label) > 10:
                    trends.append(label)
        except Exception as e:
            logger.warning(f"Pinterest page error: {e}")
        finally:
            browser.close()

    return trends[:15]


def _scrape_reddit_trends(category: dict) -> list:
    """Scrape Reddit for trending topics in relevant subreddits."""
    trends = []
    subreddits = category.get("trend_subreddits", [])

    if not subreddits:
        return []

    subreddit = random.choice(subreddits)
    # Use old.reddit.com which is easier to scrape
    url = f"https://old.reddit.com/{subreddit}/top/?t=week"

    try:
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Simple regex-based extraction of post titles
        import re

        # old.reddit titles are in <a> tags with class "title"
        title_pattern = r'class="title may-blank[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(title_pattern, response.text)

        for match in matches:
            text = match.strip()
            if len(text) > 10:
                trends.append(text)
    except Exception as e:
        logger.warning(f"Reddit scraping error: {e}")

    return trends[:10]


def _generate_ai_trend(category: dict) -> str:
    """Generate a trend using AI when scraping fails."""
    prompt = f"""Generate a single trending product design idea for the '{category["name"]}' category.
The idea should be:
- Specific and visual (something that can be turned into a graphic design)
- Currently trending or evergreen popular
- Suitable for print-on-demand products (t-shirts, mugs, hoodies)

Return ONLY the design concept in one sentence, nothing else.
Example: "A grumpy cat wearing a tiny crown with a sassy expression"
"""

    try:
        from google import genai

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_TEXT_MODEL,
            contents=prompt,
        )
        return response.text.strip().strip('"').strip("'")
    except Exception:
        pass

    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip().strip('"').strip("'")
    except Exception:
        pass

    # Ultimate fallback
    fallbacks = {
        "pets": "A cute golden retriever puppy wearing a party hat",
        "motivation": "A minimalist sunrise over mountains with determination vibes",
        "humor": "A sarcastic coffee mug character with attitude",
        "nature": "A majestic deer in a misty forest at dawn",
        "pop_culture": "A retro 80s boombox with neon colors",
        "seasonal": "A cozy autumn scene with falling leaves and warm colors",
        "abstract": "A vibrant geometric mandala pattern",
        "professions": "A superhero nurse with a stethoscope cape",
    }
    return fallbacks.get(category["name"], "A creative artistic design illustration")


def _weighted_choice(weighted_items: list) -> str:
    """Select an item with weighted probability. Each item is (value, weight)."""
    total_weight = sum(w for _, w in weighted_items)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for item, weight in weighted_items:
        cumulative += weight
        if r <= cumulative:
            return item
    return weighted_items[-1][0]


def pick_category() -> dict:
    """Pick a random design category based on weights."""
    categories = config.DESIGN_CATEGORIES
    total_weight = sum(c["weight"] for c in categories)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for cat in categories:
        cumulative += cat["weight"]
        if r <= cumulative:
            logger.info(f"Category selected: {cat['name']}")
            return cat
    return categories[-1]
