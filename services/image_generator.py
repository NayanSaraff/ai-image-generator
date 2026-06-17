"""
Image generation service layer.

Architecture:
  - Groq LLM (llama-3.3-70b-versatile)  →  refines & enriches the prompt
  - Pollinations.ai                      →  free, no-key image generation
                                            via plain CDN (never blocked)

Pollinations.ai: https://pollinations.ai  (free, no API key required)
Groq docs:       https://console.groq.com/docs
"""

from __future__ import annotations

import time
import urllib.parse
from io import BytesIO
from typing import List, Optional

import requests
from PIL import Image

from config.settings import GROQ_API_KEY, REQUEST_TIMEOUT


# ── Custom Exception ──────────────────────────────────────────────────────────

class ImageGenerationError(Exception):
    """Raised on any service failure."""


# ── Step 1: Groq prompt refinement ───────────────────────────────────────────

def _refine_prompt_with_groq(prompt: str, negative_prompt: Optional[str] = None) -> str:
    """
    Use Groq's LLM to rewrite and enrich the image prompt.
    Falls back to the original prompt if Groq key is missing or call fails.
    """
    if not GROQ_API_KEY:
        return prompt

    try:
        from groq import Groq
    except ImportError:
        return prompt

    system = (
        "You are an expert image prompt engineer. "
        "Rewrite the given prompt into a single richly detailed image generation prompt. "
        "Add specific visual details: lighting, mood, color palette, composition, texture. "
        "Output ONLY the improved prompt — no preamble, no quotes, no explanation."
    )

    user_msg = f"Original prompt: {prompt}"
    if negative_prompt:
        user_msg += f"\nExclude from image: {negative_prompt}"

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        refined = response.choices[0].message.content.strip()
        return refined if refined else prompt
    except Exception:
        return prompt  # silent fallback


# ── Step 2: Pollinations.ai image generation ──────────────────────────────────

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

_SIZE_MAP = {
    "512x512":   (512,  512),
    "1024x1024": (1024, 1024),
    "1024x1792": (1024, 1792),
}


def _fetch_pollinations_image(
    prompt: str,
    width: int,
    height: int,
    seed: int,
    negative_prompt: Optional[str] = None,
) -> Image.Image:
    """
    Fetch a single image from Pollinations.ai.

    URL format:
      https://image.pollinations.ai/prompt/{encoded_prompt}
      ?width=W&height=H&seed=S&nologo=true&enhance=true&negative={neg}
    """
    encoded_prompt = urllib.parse.quote(prompt)
    url = (
        f"{_POLLINATIONS_BASE}/{encoded_prompt}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&enhance=true"
    )
    if negative_prompt:
        url += f"&negative={urllib.parse.quote(negative_prompt)}"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.Timeout:
        raise ImageGenerationError(
            "Image generation timed out. Please try again."
        )
    except requests.HTTPError as exc:
        raise ImageGenerationError(f"Image service returned an error: {exc}")
    except requests.RequestException as exc:
        raise ImageGenerationError(f"Network error: {exc}")

    if "image" not in resp.headers.get("Content-Type", ""):
        raise ImageGenerationError(
            "Unexpected response from image service. Please try again."
        )

    return Image.open(BytesIO(resp.content)).convert("RGB")


# ── Public Interface ──────────────────────────────────────────────────────────

def generate_images(
    prompt: str,
    size: str,
    num_images: int,
    negative_prompt: Optional[str] = None,
) -> List[Image.Image]:
    """
    Generate images using Groq (prompt refinement) + Pollinations.ai (rendering).

    Pipeline:
      1. Groq LLM enriches the prompt with visual detail (skipped if no key).
      2. Pollinations.ai renders the image(s) — free, no key required.

    Args:
        prompt:          Style-enhanced prompt from prompts/styles.py.
        size:            Image dimensions string e.g. '1024x1024'.
        num_images:      Number of images to generate (1, 2, or 4).
        negative_prompt: Optional elements to exclude.

    Returns:
        List of PIL Image objects.

    Raises:
        ImageGenerationError: On network or service failures.
    """
    # Step 1 — Groq prompt enrichment (optional)
    refined_prompt = _refine_prompt_with_groq(prompt, negative_prompt)

    # Step 2 — Resolve dimensions
    width, height = _SIZE_MAP.get(size, (1024, 1024))

    # Step 3 — Generate all images (unique seed per image for variety)
    base_seed = int(time.time())
    images: List[Image.Image] = []

    for i in range(num_images):
        img = _fetch_pollinations_image(
            prompt=refined_prompt,
            width=width,
            height=height,
            seed=base_seed + i,
            negative_prompt=negative_prompt,
        )
        print("Requested:", width, "x", height)
        print("Received:", img.size)
        images.append(img)

    return images


def get_refined_prompt(prompt: str, negative_prompt: Optional[str] = None) -> str:
    """Expose the Groq-refined prompt so the UI can display it."""
    return _refine_prompt_with_groq(prompt, negative_prompt)
