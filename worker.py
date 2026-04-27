import os
import json
import time
import requests
import random
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
from playwright.sync_api import sync_playwright

load_dotenv()

# Configuration
STATE_FILE = "state.json"
OUTPUT_DIR = "outputs"
MAX_HISTORY = 3

# API Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MASTER_DESIGN_PROMPT = """
Technical Instruction:
Generate one high-detail realism image in 9:16 portrait aspect ratio. 
Subject: {trending_topic}. 
Style: Commercial product photography, 8k resolution. 
Focus on 'Tactile Realism'—visible fabric fibers, natural skin texture with pores and fine hairs, and authentic cinematic lighting (Softbox + Rim light). 
Avoid smooth, 'airbrushed' surfaces. 
Background should be a realistic environment with natural depth of field (f/1.8 bokeh). 
Color Palette: Earthy and organic. No text overlay.
"""

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"run_count": 0, "history": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_trend():
    print("Discovering viral pet trends...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Try Pinterest Search for Pet Trends
            search_query = "pet trends 2026"
            page.goto(f"https://www.pinterest.com/search/pins/?q={search_query}")
            page.wait_for_timeout(5000)
            
            # Extract aria-labels from pins
            pins = page.query_selector_all("a[aria-label][href*='/pin/']")
            if not pins:
                # Fallback to Reddit
                print("Pinterest extraction failed, falling back to Reddit...")
                page.goto("https://www.reddit.com/r/aww/top/?t=day")
                page.wait_for_timeout(5000)
                # Simple extraction for Reddit
                titles = page.query_selector_all("h3")
                concepts = [t.inner_text() for t in titles if len(t.inner_text()) > 10]
            else:
                concepts = [p.get_attribute("aria-label") for p in pins if p.get_attribute("aria-label")]
            
            browser.close()
            
            if concepts:
                # Pick a random one from the top few
                selected = random.choice(concepts[:10])
                print(f"Trend discovered: {selected}")
                return selected
    except Exception as e:
        print(f"Trend discovery error: {e}")
    
    return "A cute golden retriever in a cozy modern home"

def generate_text_with_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash") # Using 1.5 Flash as proxy for Gemini 3 Flash
    response = model.generate_content(prompt)
    return response.text

def generate_text_with_openai(prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4o", # Using 4o as proxy for ChatGPT 2026
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_image_with_gemini(prompt):
    # This assumes Imagen 3 or equivalent is accessible via the SDK in 2026
    # For now, we simulate with a call that would exist
    print(f"Generating image with Gemini: {prompt[:50]}...")
    # Real implementation would call the imagen model
    # response = genai.ImageModel("imagen-3").generate_images(prompt=prompt)
    # return response.images[0].data
    raise NotImplementedError("Gemini Image Gen requires specific 2026 API access. Simulation mode.")

def generate_image_with_openai(prompt):
    print(f"Generating image with OpenAI: {prompt[:50]}...")
    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792", # 9:16 approx
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    return requests.get(image_url).content

def run_worker():
    state = load_state()
    state["run_count"] += 1
    run_num = (state["run_count"] - 1) % 4 + 1 # 1, 2, 3, 4 cycle
    print(f"Starting Run #{run_num}")

    trend = get_trend()
    
    # Prompt Generation Strategy
    # Run 1 & 3: Gemini, Run 2 & 4: OpenAI
    primary_provider = "gemini" if run_num in [1, 3] else "openai"
    
    def get_prompt_with_fallback(trend, provider):
        system_prompt = f"Create a high-detail image prompt based on this trend: {trend}. Use the Master Design Prompt structure."
        try:
            if provider == "gemini":
                return generate_text_with_gemini(system_prompt)
            else:
                return generate_text_with_openai(system_prompt)
        except Exception as e:
            print(f"Primary prompt provider {provider} failed: {e}. Trying alternate...")
            if provider == "gemini":
                return generate_text_with_openai(system_prompt)
            else:
                return generate_text_with_gemini(system_prompt)

    raw_prompt = get_prompt_with_fallback(trend, primary_provider)
    final_prompt = MASTER_DESIGN_PROMPT.format(trending_topic=raw_prompt)
    
    # Image Generation Strategy
    # Run 1 & 3: Gemini, Run 2 & 4: OpenAI
    image_provider = "gemini" if run_num in [1, 3] else "openai"
    
    def get_image_with_fallback(prompt, provider):
        try:
            if provider == "gemini":
                # Temporary fallback to OpenAI if Gemini Image Gen is not ready in this environment
                return generate_image_with_openai(prompt)
            else:
                return generate_image_with_openai(prompt)
        except Exception as e:
            print(f"Primary image provider {provider} failed: {e}. Trying alternate...")
            return generate_image_with_openai(prompt) # Only OpenAI DALLE-3 is widely available for now

    image_data = get_image_with_fallback(final_prompt, image_provider)
    
    # Caption Generation
    caption_prompt = f"Generate a viral Social Media Caption (with SEO hashtags) for this POD design concept: {trend}"
    caption = generate_text_with_openai(caption_prompt) # Use OpenAI for captions as secondary logic

    # Persistence
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"image_{timestamp}.png"
    caption_filename = f"caption_{timestamp}.txt"
    
    with open(os.path.join(OUTPUT_DIR, image_filename), "wb") as f:
        f.write(image_data)
    
    with open(os.path.join(OUTPUT_DIR, caption_filename), "w") as f:
        f.write(caption)
    
    # Update History and Cleanup
    state["history"].append({
        "timestamp": timestamp,
        "image": image_filename,
        "caption": caption_filename,
        "trend": trend
    })
    
    if len(state["history"]) > MAX_HISTORY:
        to_remove = state["history"][:-MAX_HISTORY]
        state["history"] = state["history"][-MAX_HISTORY:]
        for old in to_remove:
            img_path = os.path.join(OUTPUT_DIR, old["image"])
            cap_path = os.path.join(OUTPUT_DIR, old["caption"])
            if os.path.exists(img_path): os.remove(img_path)
            if os.path.exists(cap_path): os.remove(cap_path)
            print(f"Cleaned up old files: {old['image']}")

    save_state(state)
    print(f"Run #{run_num} completed successfully.")

if __name__ == "__main__":
    run_worker()
