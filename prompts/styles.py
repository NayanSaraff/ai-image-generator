"""
Style-conditioned prompt templates.
Each style appends descriptive modifiers to the user's base prompt
to guide the image generation model toward the desired aesthetic.
"""

from typing import Dict

# ── Style Templates ───────────────────────────────────────────────────────────
# {prompt} is replaced at runtime with the user's input.
STYLE_TEMPLATES: Dict[str, str] = {
    "Realistic": (
        "{prompt}, photorealistic, ultra high definition, natural lighting, "
        "detailed textures, shot on DSLR camera, 8K resolution"
    ),
    "Anime": (
        "{prompt}, anime style, highly detailed, vibrant colors, "
        "cinematic lighting, Studio Ghibli inspired, cel shading"
    ),
    "Cyberpunk": (
        "{prompt}, cyberpunk aesthetic, neon lights, dark atmosphere, "
        "futuristic cityscape, rain-slicked streets, high contrast, "
        "blade runner vibes, 4K"
    ),
    "Fantasy": (
        "{prompt}, epic fantasy art, magical atmosphere, intricate details, "
        "mystical lighting, dragons and castles, digital painting, "
        "artstation trending"
    ),
    "Watercolor": (
        "{prompt}, watercolor painting style, soft edges, flowing colors, "
        "delicate brush strokes, pastel palette, artistic, dreamy"
    ),
    "3D Render": (
        "{prompt}, 3D render, octane render, hyper realistic, ray tracing, "
        "studio lighting, smooth surfaces, ultra detailed, Blender"
    ),
}

# Ordered list for UI display
STYLE_NAMES: list[str] = list(STYLE_TEMPLATES.keys())


def build_prompt(user_prompt: str, style: str, negative_prompt: str = "") -> tuple[str, str]:
    """
    Combine the user's base prompt with the selected style template.

    Args:
        user_prompt:     Raw text entered by the user.
        style:           One of the keys in STYLE_TEMPLATES.
        negative_prompt: Optional elements to exclude from the image.

    Returns:
        A tuple of (enhanced_positive_prompt, negative_prompt).
    """
    template = STYLE_TEMPLATES.get(style, "{prompt}")
    enhanced = template.format(prompt=user_prompt.strip())
    return enhanced, negative_prompt.strip()
