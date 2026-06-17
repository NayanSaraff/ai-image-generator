"""
Prompt history management using Streamlit session state.
Each history entry captures the prompt, style, timestamp, and
the actual generated PIL images (stored as PNG bytes for efficiency).
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image

HISTORY_KEY = "prompt_history"


def init_history() -> None:
    """Initialise the history list in session state if not present."""
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []


def _images_to_bytes(images: List[Image.Image]) -> List[bytes]:
    """Convert a list of PIL Images to PNG bytes for session storage."""
    result = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())
    return result


def bytes_to_images(image_bytes_list: List[bytes]) -> List[Image.Image]:
    """Convert stored PNG bytes back to PIL Images for display."""
    return [Image.open(io.BytesIO(b)) for b in image_bytes_list]


def add_to_history(
    prompt: str,
    style: str,
    num_images: int,
    images: Optional[List[Image.Image]] = None,
) -> None:
    """
    Prepend a new entry to the prompt history, including generated images.

    Args:
        prompt:     The original user-entered prompt.
        style:      The style selected by the user.
        num_images: Number of images requested.
        images:     The actual generated PIL Image objects.
    """
    init_history()
    entry: Dict[str, Any] = {
        "prompt": prompt,
        "style": style,
        "num_images": num_images,
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M"),
        "image_bytes": _images_to_bytes(images) if images else [],
    }
    st.session_state[HISTORY_KEY].insert(0, entry)


def get_history() -> List[Dict[str, Any]]:
    """Return the full prompt history list (newest first)."""
    init_history()
    return st.session_state[HISTORY_KEY]


def clear_history() -> None:
    """Wipe all stored history entries including images."""
    st.session_state[HISTORY_KEY] = []
