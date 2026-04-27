"""
POD Automation Pipeline — Centralized Configuration
All settings, platform toggles, design categories, and constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# API Keys & Credentials
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PRINTIFY_API_TOKEN = os.getenv("PRINTIFY_API_TOKEN", "")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID", "")
REDBUBBLE_EMAIL = os.getenv("REDBUBBLE_EMAIL", "")
REDBUBBLE_PASSWORD = os.getenv("REDBUBBLE_PASSWORD", "")
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID", "")

# ──────────────────────────────────────────────
# Platform Toggles (auto-enabled if credentials exist)
# ──────────────────────────────────────────────
ENABLE_PRINTIFY = bool(PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID)
ENABLE_REDBUBBLE = bool(REDBUBBLE_EMAIL and REDBUBBLE_PASSWORD)
ENABLE_PINTEREST = bool(PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID)

# ──────────────────────────────────────────────
# File Paths
# ──────────────────────────────────────────────
STATE_FILE = "state.json"
OUTPUT_DIR = "outputs"
MOCKUP_DIR = "outputs/mockups"
LOG_DIR = "logs"

# ──────────────────────────────────────────────
# Design Categories (weighted random selection)
# Higher weight = more likely to be picked
# ──────────────────────────────────────────────
DESIGN_CATEGORIES = [
    {
        "name": "pets",
        "weight": 2,
        "styles": [
            "cute cartoon pet portrait",
            "funny animal character illustration",
            "realistic pet breed artwork",
            "pet with sunglasses pop art",
        ],
        "trend_subreddits": ["r/aww", "r/rarepuppers", "r/cats"],
        "trend_keywords": ["cute pets", "dog breeds", "funny cats"],
    },
    {
        "name": "motivation",
        "weight": 2,
        "styles": [
            "bold typography motivational quote",
            "minimalist inspirational design",
            "retro vintage motivational poster",
            "hand-lettered quote artwork",
        ],
        "trend_subreddits": ["r/GetMotivated", "r/quotes"],
        "trend_keywords": ["motivational quotes", "inspirational sayings"],
    },
    {
        "name": "humor",
        "weight": 3,
        "styles": [
            "sarcastic text-based design",
            "funny dad joke illustration",
            "meme-inspired graphic design",
            "witty one-liner typography",
        ],
        "trend_subreddits": ["r/funny", "r/memes"],
        "trend_keywords": ["funny shirts", "sarcastic quotes", "dad jokes"],
    },
    {
        "name": "nature",
        "weight": 1,
        "styles": [
            "watercolor botanical illustration",
            "mountain landscape minimal art",
            "wildlife portrait illustration",
            "floral pattern design",
        ],
        "trend_subreddits": ["r/EarthPorn", "r/NatureIsFuckingLit"],
        "trend_keywords": ["nature art", "botanical prints", "landscape design"],
    },
    {
        "name": "pop_culture",
        "weight": 2,
        "styles": [
            "retro 80s nostalgia graphic",
            "pixel art gaming design",
            "anime-inspired character art",
            "vaporwave aesthetic design",
        ],
        "trend_subreddits": ["r/gaming", "r/retrogaming", "r/anime"],
        "trend_keywords": ["retro gaming", "nostalgia", "pop culture trends"],
    },
    {
        "name": "seasonal",
        "weight": 1,
        "styles": [
            "holiday themed festive design",
            "summer vibes tropical art",
            "autumn cozy aesthetic",
            "spring floral celebration",
        ],
        "trend_subreddits": [],
        "trend_keywords": ["holiday designs", "seasonal trends"],
    },
    {
        "name": "abstract",
        "weight": 1,
        "styles": [
            "geometric abstract pattern",
            "watercolor splash artwork",
            "minimalist line art",
            "psychedelic trippy design",
        ],
        "trend_subreddits": ["r/AbstractArt", "r/Art"],
        "trend_keywords": ["abstract art", "geometric design", "modern art"],
    },
    {
        "name": "professions",
        "weight": 2,
        "styles": [
            "nurse life funny design",
            "teacher appreciation graphic",
            "software developer humor",
            "coffee-obsessed office worker",
            "gym and fitness lifestyle",
        ],
        "trend_subreddits": ["r/nursing", "r/Teachers", "r/ProgrammerHumor"],
        "trend_keywords": ["nurse shirts", "teacher gifts", "programmer humor", "gym shirts"],
    },
]

# ──────────────────────────────────────────────
# Image Generation Settings
# ──────────────────────────────────────────────
IMAGE_MIN_WIDTH = 4500       # Minimum width for print quality
IMAGE_MIN_HEIGHT = 5400      # Minimum height for print quality
IMAGE_FORMAT = "PNG"         # Always PNG for transparency
REMOVE_BACKGROUND = True     # Run rembg background removal

# Gemini Imagen model
GEMINI_IMAGE_MODEL = "imagen-3.0-generate-002"
# Gemini text model
GEMINI_TEXT_MODEL = "gemini-2.0-flash"

# ──────────────────────────────────────────────
# POD Master Design Prompt Template
# ──────────────────────────────────────────────
MASTER_DESIGN_PROMPT = """
You are a professional print-on-demand graphic designer.
Create a single, high-quality design based on:

Topic/Trend: {trend}
Style: {style}
Category: {category}

CRITICAL REQUIREMENTS:
- The design MUST be on a PURE WHITE background (#FFFFFF)
- Subject must be completely isolated and centered
- NO text, NO words, NO letters in the design
- NO borders, NO frames, NO background patterns
- Clean, crisp edges around the subject
- High detail, vibrant colors, professional quality
- Design should look great on a t-shirt, hoodie, or mug
- Think "best seller on Etsy/Redbubble" quality level

OUTPUT: Return ONLY a detailed image generation prompt, nothing else.
"""

# ──────────────────────────────────────────────
# Printify Configuration
# ──────────────────────────────────────────────
PRINTIFY_BASE_URL = "https://api.printify.com/v1"

# Product blueprints to create for each design
# Format: (blueprint_id, print_provider_id, description)
# These are common Printify product types
PRINTIFY_PRODUCTS = [
    {"blueprint_id": 6, "print_provider_id": 99, "name": "Unisex Gildan T-Shirt"},
    {"blueprint_id": 77, "print_provider_id": 99, "name": "Unisex Hoodie"},
    {"blueprint_id": 638, "print_provider_id": 99, "name": "White Glossy Mug"},
]

# Base price markup (cents) — your profit margin
PRINTIFY_PRICE_MARKUP = 500  # $5.00 profit per item

# ──────────────────────────────────────────────
# Redbubble Configuration (Browser Automation)
# ──────────────────────────────────────────────
REDBUBBLE_MAX_UPLOADS_PER_RUN = 3
REDBUBBLE_MIN_DELAY = 30     # seconds between uploads
REDBUBBLE_MAX_DELAY = 60     # seconds between uploads

# ──────────────────────────────────────────────
# Pipeline Settings
# ──────────────────────────────────────────────
MAX_HISTORY = 50             # Keep last N designs in state
MAX_RETRIES = 3              # Max retries per operation
RETRY_DELAY = 5              # Base delay between retries (seconds)
DESIGNS_PER_RUN = 1          # Number of designs to generate per run
