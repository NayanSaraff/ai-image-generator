"""
Application configuration and settings.
Loads environment variables and defines global constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
# Groq is used for prompt refinement (optional).
# Pollinations.ai requires NO API key.
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# ── Groq model for prompt refinement ─────────────────────────────────────────
GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"

# ── Image Generation Defaults ─────────────────────────────────────────────────
DEFAULT_IMAGE_SIZE: str = "1024x1024"
DEFAULT_NUM_IMAGES: int = 1
REQUEST_TIMEOUT: int    = 90

# ── Supported Image Sizes ─────────────────────────────────────────────────────
IMAGE_SIZES: list[str] = [
    "512x512",       # Small / fast
    "768x768",       # Medium square
    "1024x1024",     # Large square (default)
    "1280x720",      # Landscape (16:9)
    "1024x1792",     # Portrait (9:16)
    "1920x1080",     # Full HD landscape
]

# ── App Meta ──────────────────────────────────────────────────────────────────
APP_TITLE: str = "🎨 AI Image Generator"
APP_DESCRIPTION: str = (
    "Transform your text descriptions into stunning AI-generated images. "
    "Groq refines your prompt — Pollinations.ai renders the image. "
    "No image API key required."
)
