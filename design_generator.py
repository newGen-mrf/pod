"""
POD Automation Pipeline — Design Generator
Handles AI image generation (Gemini Imagen 3 + DALL-E 3 fallback),
background removal, and resolution upscaling for print-ready output.
"""

import io
import os
import time
import logging
import requests
from PIL import Image

import config

logger = logging.getLogger("pod.design")


def generate_design(trend: str, category: dict) -> str:
    """
    Full pipeline: generate prompt → generate image → remove bg → upscale → save.
    Returns the path to the final print-ready PNG.
    """
    import random

    style = random.choice(category["styles"])
    logger.info(f"Generating design | Category: {category['name']} | Style: {style}")

    # Step 1: Generate the detailed image prompt using AI
    image_prompt = _generate_image_prompt(trend, style, category["name"])
    logger.info(f"Image prompt generated ({len(image_prompt)} chars)")

    # Step 2: Generate the actual image
    image_data = _generate_image(image_prompt)
    logger.info("Raw image generated successfully")

    # Step 3: Remove background
    if config.REMOVE_BACKGROUND:
        image_data = _remove_background(image_data)
        logger.info("Background removed")

    # Step 4: Ensure print-ready resolution
    image_data = _ensure_resolution(image_data)
    logger.info("Resolution verified/upscaled")

    # Step 5: Save to outputs
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"design_{timestamp}.png"
    filepath = os.path.join(config.OUTPUT_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(image_data)

    logger.info(f"Design saved: {filepath}")
    return filepath


def _prompt_with_groq(prompt: str) -> str:
    """Generate text prompt using Groq."""
    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=config.GROQ_MODEL,
    )
    return chat_completion.choices[0].message.content.strip()


def _generate_image_prompt(trend: str, style: str, category_name: str) -> str:
    """Use AI to create a detailed image generation prompt."""
    system_prompt = config.MASTER_DESIGN_PROMPT.format(
        trend=trend, style=style, category=category_name
    )

    # Multi-Provider Fallback Order: Groq -> Gemini -> OpenAI Primary -> OpenAI Secondary
    for attempt in range(config.MAX_RETRIES):
        # 1. Try Groq (Best for free tier stability)
        if config.GROQ_API_KEY:
            try:
                return _prompt_with_groq(system_prompt)
            except Exception as e:
                logger.warning(f"Groq text gen failed (attempt {attempt + 1}): {e}")

        # 2. Try Gemini
        if config.GEMINI_API_KEY:
            try:
                return _prompt_with_gemini(system_prompt)
            except Exception as e:
                logger.warning(f"Gemini text gen failed (attempt {attempt + 1}): {e}")

        # 3. Try all available OpenAI keys
        for key_name, key in [("Primary", config.OPENAI_API_KEY), ("Secondary", config.OPENAI_API_KEY_2)]:
            if not key:
                continue
            try:
                return _prompt_with_openai(system_prompt, key)
            except Exception as e:
                logger.warning(f"OpenAI {key_name} text gen failed (attempt {attempt + 1}): {e}")

        if attempt < config.MAX_RETRIES - 1:
            time.sleep(config.RETRY_DELAY * (attempt + 1))

    raise RuntimeError("All text generation providers failed")


def _prompt_with_gemini(prompt: str) -> str:
    """Generate text prompt using Gemini."""
    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_TEXT_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def _prompt_with_openai(prompt: str, api_key: str) -> str:
    """Generate text prompt using OpenAI with specific key."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _generate_image(prompt: str) -> bytes:
    """
    Generate an image from the prompt.
    Tries Gemini Imagen 3 first, then DALL-E 3 as fallback.
    """
    errors = []

    # Attempt 1: Gemini Imagen 3
    if config.GEMINI_API_KEY:
        try:
            return _image_with_gemini(prompt)
        except Exception as e:
            errors.append(f"Gemini Imagen: {e}")
            logger.warning(f"Gemini image gen failed: {e}")

    # Attempt 2: OpenAI DALL-E 3 (Try all keys)
    for key_name, key in [("Primary", config.OPENAI_API_KEY), ("Secondary", config.OPENAI_API_KEY_2)]:
        if not key:
            continue
        try:
            return _image_with_openai(prompt, key)
        except Exception as e:
            errors.append(f"DALL-E 3 {key_name}: {e}")
            logger.warning(f"OpenAI {key_name} image gen failed: {e}")

    # Attempt 3: Pollinations.ai (Absolute Fallback — Free and No-Key)
    try:
        return _image_with_pollinations(prompt)
    except Exception as e:
        errors.append(f"Pollinations: {e}")
        logger.warning(f"Pollinations image gen failed: {e}")

    raise RuntimeError(f"All image generators failed: {'; '.join(errors)}")


def _image_with_gemini(prompt: str) -> bytes:
    """Generate image using Google Imagen 3 via the google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    # Add POD-specific instructions to the prompt
    pod_prompt = (
        f"{prompt}. "
        "Pure white background, isolated subject, no text, "
        "clean crisp edges, high detail, vibrant colors, "
        "professional print-on-demand quality."
    )

    response = client.models.generate_images(
        model=config.GEMINI_IMAGE_MODEL,
        prompt=pod_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
        ),
    )

    if response.generated_images:
        return response.generated_images[0].image.image_bytes
    raise RuntimeError("Gemini returned no images")


def _image_with_pollinations(prompt: str) -> bytes:
    """Generate image using Pollinations.ai (Free, No-Key fallback)."""
    import urllib.parse
    
    # Clean the prompt for URL
    encoded_prompt = urllib.parse.quote(prompt)
    width, height = 1024, 1024
    seed = int(time.time())
    
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true&enhance=true"
    
    logger.info(f"Using Pollinations fallback: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def _image_with_openai(prompt: str, api_key: str) -> bytes:
    """Generate image using OpenAI DALL-E 3 with specific key."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    # Add POD-specific instructions
    pod_prompt = (
        f"{prompt}. "
        "Isolated on a pure white background, centered composition, "
        "no text or letters, clean edges, high detail, "
        "professional illustration quality suitable for print-on-demand products."
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt=pod_prompt,
        size="1024x1792",  # Closest to 9:16 portrait for POD
        quality="hd",
        n=1,
    )

    image_url = response.data[0].url
    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()
    return img_response.content


def _remove_background(image_data: bytes) -> bytes:
    """Remove background using rembg to create transparent PNG."""
    try:
        from rembg import remove

        output = remove(image_data)
        logger.info("Background removed with rembg")
        return output
    except ImportError:
        logger.warning("rembg not installed — skipping background removal")
        return image_data
    except Exception as e:
        logger.warning(f"Background removal failed: {e} — using original image")
        return image_data


def _auto_crop(image_data: bytes) -> bytes:
    """Crop the transparent padding out to ensure maximum size on Printify."""
    try:
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            logger.info("Image auto-cropped to non-transparent bounding box")
            return buffer.getvalue()
        return image_data
    except Exception as e:
        logger.warning(f"Auto-crop failed: {e}")
        return image_data


def _ensure_resolution(image_data: bytes, min_width=None, min_height=None) -> bytes:
    """
    Ensure the image meets minimum print resolution.
    Upscales using Lanczos resampling if needed.
    """
    min_width = min_width or config.IMAGE_MIN_WIDTH
    min_height = min_height or config.IMAGE_MIN_HEIGHT

    img = Image.open(io.BytesIO(image_data))

    if img.width >= min_width and img.height >= min_height:
        return image_data  # Already large enough

    # Calculate scale factor to meet minimums
    scale_w = min_width / img.width if img.width < min_width else 1
    scale_h = min_height / img.height if img.height < min_height else 1
    scale = max(scale_w, scale_h)

    new_width = int(img.width * scale)
    new_height = int(img.height * scale)

    logger.info(f"Upscaling from {img.width}x{img.height} to {new_width}x{new_height}")
    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Save back to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
