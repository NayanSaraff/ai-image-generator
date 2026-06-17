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
DEFAULT_IMAGE_SIZE: str = "256x256"
DEFAULT_NUM_IMAGES: int = 1
REQUEST_TIMEOUT: int    = 90

# ── App Meta ──────────────────────────────────────────────────────────────────
APP_TITLE: str = "🎨 AI Image Generator"
APP_DESCRIPTION: str = (
    "Transform your text descriptions into stunning AI-generated images. "
    "Groq refines your prompt — Pollinations.ai renders the image. "
)
