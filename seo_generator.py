"""
POD Automation Pipeline — SEO & Caption Generator
Generates platform-optimized titles, descriptions, tags, and social captions.
"""

import logging
import time

import config

logger = logging.getLogger("pod.seo")


def generate_seo(trend: str, category: dict) -> dict:
    """
    Generate all SEO content for a design.
    Returns dict with: title, description, tags, pinterest_caption
    """
    logger.info(f"Generating SEO content for: {trend}")

    prompt = _build_seo_prompt(trend, category["name"])

    # Try Gemini first (cheaper/faster), fallback to OpenAI
    raw_output = None
    for attempt in range(config.MAX_RETRIES):
        try:
            raw_output = _generate_with_gemini(prompt)
            break
        except Exception as e:
            logger.warning(f"Gemini SEO gen failed (attempt {attempt + 1}): {e}")

        try:
            raw_output = _generate_with_openai(prompt)
            break
        except Exception as e:
            logger.warning(f"OpenAI SEO gen failed (attempt {attempt + 1}): {e}")

        if attempt < config.MAX_RETRIES - 1:
            time.sleep(config.RETRY_DELAY * (attempt + 1))

    if not raw_output:
        logger.error("All SEO providers failed — using defaults")
        return _default_seo(trend, category["name"])

    return _parse_seo_output(raw_output, trend, category["name"])


def _build_seo_prompt(trend: str, category_name: str) -> str:
    return f"""You are an expert Print-on-Demand SEO specialist. Generate optimized listing content for a POD design.

Design Topic: {trend}
Category: {category_name}

Generate the following in EXACTLY this format (keep the labels):

TITLE: [A catchy, SEO-optimized product title, max 140 characters. Include main keywords naturally. Think "best seller on Etsy".]

DESCRIPTION: [A compelling product description, 2-3 sentences. Highlight the design appeal, who it's perfect for as a gift, and quality. Include relevant keywords naturally.]

TAGS: [Exactly 13 comma-separated tags. Mix broad and niche keywords. No hashtags, just words/phrases.]

PINTEREST: [A viral Pinterest pin description, 2-3 sentences with 5 relevant hashtags. Make it engaging and clickable.]

IMPORTANT:
- Do NOT use generic filler words
- Tags should be specific and searchable
- Title must grab attention immediately
- Pinterest caption should drive clicks"""


def _generate_with_gemini(prompt: str) -> str:
    """Generate SEO content using Gemini."""
    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_TEXT_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def _generate_with_openai(prompt: str) -> str:
    """Generate SEO content using OpenAI."""
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _parse_seo_output(raw: str, trend: str, category: str) -> dict:
    """Parse the structured SEO output into a dict."""
    result = {
        "title": "",
        "description": "",
        "tags": [],
        "pinterest_caption": "",
    }

    lines = raw.strip().split("\n")
    current_key = None
    current_value = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        upper = line.upper()
        if upper.startswith("TITLE:"):
            if current_key:
                result[current_key] = _join_value(current_value)
            current_key = "title"
            current_value = [line.split(":", 1)[1].strip()]
        elif upper.startswith("DESCRIPTION:"):
            if current_key:
                result[current_key] = _join_value(current_value)
            current_key = "description"
            current_value = [line.split(":", 1)[1].strip()]
        elif upper.startswith("TAGS:"):
            if current_key:
                result[current_key] = _join_value(current_value)
            current_key = "tags"
            current_value = [line.split(":", 1)[1].strip()]
        elif upper.startswith("PINTEREST:"):
            if current_key:
                result[current_key] = _join_value(current_value)
            current_key = "pinterest_caption"
            current_value = [line.split(":", 1)[1].strip()]
        else:
            if current_key:
                current_value.append(line)

    # Flush last key
    if current_key:
        result[current_key] = _join_value(current_value)

    # Parse tags from comma-separated string
    if isinstance(result["tags"], str):
        result["tags"] = [
            t.strip().strip("#").strip()
            for t in result["tags"].split(",")
            if t.strip()
        ]

    # Truncate title to 140 chars
    if len(result["title"]) > 140:
        result["title"] = result["title"][:137] + "..."

    # Ensure we have at least something
    if not result["title"]:
        result = _default_seo(trend, category)

    logger.info(f"SEO generated — Title: {result['title'][:60]}... | Tags: {len(result['tags'])}")
    return result


def _join_value(parts: list) -> str:
    return " ".join(parts).strip()


def _default_seo(trend: str, category: str) -> dict:
    """Fallback SEO content if AI generation fails."""
    clean_trend = trend[:100]
    return {
        "title": f"{clean_trend} | Unique {category.title()} Design",
        "description": (
            f"Express yourself with this unique {category} design inspired by "
            f"{clean_trend}. Perfect as a gift or for personal style."
        ),
        "tags": [
            category,
            clean_trend.split()[0] if clean_trend.split() else category,
            "graphic design",
            "unique design",
            "gift idea",
            "funny shirt",
            "cool design",
            "trending",
            "print on demand",
            "custom shirt",
            "art print",
            "illustration",
            "creative",
        ],
        "pinterest_caption": (
            f"Check out this amazing {category} design! 🔥 "
            f"Inspired by {clean_trend}. Perfect gift for any occasion. "
            f"#Design #{category.title()} #GiftIdea #PrintOnDemand #Trending"
        ),
    }
