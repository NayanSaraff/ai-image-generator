"""
Random creative prompt bank.
Provides a diverse set of imaginative prompts to inspire users.
"""

import random
from typing import List

RANDOM_PROMPTS: List[str] = [
    # Architecture & Landscapes
    "Ancient temple floating above the clouds at golden hour",
    "A futuristic Indian city at night with towering spires",
    "Abandoned Victorian mansion overgrown with luminescent vines",
    "Underwater city built inside a giant coral reef",
    "A medieval marketplace on the surface of Mars",
    "Himalayan monastery suspended on a levitating rock",

    # Characters & Creatures
    "Robot chef cooking in a futuristic neon-lit kitchen",
    "A warrior princess riding a mechanical elephant",
    "Dragon flying through a cyberpunk city during a storm",
    "An astronaut meditating in a lotus position on the moon",
    "Ancient samurai standing in a field of cherry blossoms",
    "A friendly alien shopkeeper in a space bazaar",

    # Nature & Surreal
    "Bioluminescent forest where every tree glows blue at midnight",
    "Giant sunflowers as tall as skyscrapers in a golden field",
    "Aurora borealis reflected in a perfectly still Arctic lake",
    "A whale swimming through clouds above mountain peaks",
    "Crystal cave with rainbow light refracting through stalactites",
    "Desert sand dunes that transform into ocean waves at sunset",

    # Abstract & Concept
    "The concept of music visualised as colorful sound waves",
    "Time flowing like a river through an hourglass landscape",
    "A library that exists between dimensions with infinite books",
    "City of mirrors where every reflection shows a different world",
    "A clock melting over a surrealist dreamscape",
    "Universe inside a glass bottle on a wooden shelf",

    # Food & Everyday Surreal
    "A giant samosa floating in outer space with stars",
    "A cozy café on the back of a giant turtle",
    "Street food stall run by robots in 2150 Mumbai",
    "Tea garden that grows in the clouds above a mountain",
]


def get_random_prompt() -> str:
    """Return a single random prompt from the bank."""
    return random.choice(RANDOM_PROMPTS)
