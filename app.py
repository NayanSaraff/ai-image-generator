"""
AI Image Generation Chatbot — main Streamlit entry point.

Responsibilities:
  • Render the UI (title, controls, results, sidebar history + image gallery).
  • Delegate API calls to services/image_generator.py.
  • Delegate prompt building to prompts/styles.py.
  • Delegate history (with image storage) to utils/history.py.
  • Delegate random prompts to utils/random_prompts.py.
"""

from __future__ import annotations

import io
from typing import List

import streamlit as st
from PIL import Image

from config.settings import (
    APP_DESCRIPTION,
    APP_TITLE,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_NUM_IMAGES,
    GROQ_API_KEY,
)
from prompts.styles import STYLE_NAMES, build_prompt
from services.image_generator import ImageGenerationError, generate_images, get_refined_prompt
from utils.history import (
    add_to_history,
    bytes_to_images,
    clear_history,
    get_history,
    init_history,
)
from utils.random_prompts import get_random_prompt

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session-state initialisation ──────────────────────────────────────────────
init_history()
if "theme" not in st.session_state:
    st.session_state["theme"] = "Dark"
if "random_prompt" not in st.session_state:
    st.session_state["random_prompt"] = ""
if "gallery_index" not in st.session_state:
    st.session_state["gallery_index"] = None  # index of history entry being viewed





# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .hero-title   { font-size: 5rem !important; font-weight: 900; letter-spacing: -0.5px; text-align: center }
    .hero-sub     { font-size: 1.2rem !important; opacity: 0.75; margin-bottom: 1.5rem; text-align: center}
    .hist-item    { padding: 0.55rem 0.75rem; border-radius: 8px;
                    background: rgba(124,58,237,0.12); margin-bottom: 0.4rem; }
    .hist-style   { font-size: 0.72rem; opacity: 0.65; }
    .hist-ts      { font-size: 0.68rem; opacity: 0.5; }
    .gallery-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; }
    div[data-testid="stButton"] > button { border-radius: 8px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helper: image → download bytes ───────────────────────────────────────────
def _img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Helper: render an image grid with download buttons ───────────────────────
def _render_image_grid(images: List[Image.Image], key_prefix: str = "img") -> None:
    cols = st.columns(1 if len(images) == 1 else 2)
    for idx, img in enumerate(images):
        with cols[idx % len(cols)]:
            st.image(img, use_container_width=True, caption=f"Image {idx + 1}")
            st.download_button(
                label=f"⬇️ Download Image {idx + 1}",
                data=_img_to_bytes(img),
                file_name=f"{key_prefix}_{idx + 1}.png",
                mime="image/png",
                use_container_width=True,
                key=f"{key_prefix}_dl_{idx}",
            )


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
  
    # ── Image History & Gallery ───────────────────────────────────────────────
    st.markdown("## 🖼️ Image Gallery")
    history = get_history()

    if history:
        col_clear, col_back = st.columns(2)
        with col_clear:
            if st.button("🗑️ Clear All", width='stretch'):
                clear_history()
                st.session_state["gallery_index"] = None
                st.rerun()
        with col_back:
            if st.session_state["gallery_index"] is not None:
                if st.button("↩️ Back", use_container_width=True):
                    st.session_state["gallery_index"] = None
                    st.rerun()

        st.markdown("---")

        for i, entry in enumerate(history):
            has_images = bool(entry.get("image_bytes"))

            # Show thumbnail of first image if available
            # if has_images:
            #     thumb_bytes = entry["image_bytes"][0]
            #     thumb = Image.open(io.BytesIO(thumb_bytes))
            #     thumb.thumbnail((300, 300))
            #     st.image(thumb, use_container_width=True)

            st.markdown(
                f"""
                <div class="hist-item">
                  <div><strong>{entry['prompt'][:55]}{'…' if len(entry['prompt']) > 55 else ''}</strong></div>
                  <div class="hist-style">🎨 {entry['style']} &nbsp;·&nbsp; 🖼️ {entry['num_images']} img</div>
                  <div class="hist-ts">🕐 {entry['timestamp']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if has_images:
                if st.button(
                    f"👁️ View Images",
                    key=f"view_{i}",
                    use_container_width=True,
                ):
                    st.session_state["gallery_index"] = i
                    st.rerun()

            st.markdown("")  # spacing

    else:
        st.info("No history yet. Generate your first image!", icon="💡")


# ─────────────────────────────────────────────────────────────────────────────
# GALLERY VIEW — shown in main area when user clicks "View Images"
# ─────────────────────────────────────────────────────────────────────────────
gallery_idx = st.session_state.get("gallery_index")

if gallery_idx is not None and history:
    entry = history[gallery_idx]
    recalled_images = bytes_to_images(entry["image_bytes"])

    st.markdown(f'<p class="hero-title">🖼️ Saved Images</p>', unsafe_allow_html=True)
    st.markdown(
        f"**Prompt:** {entry['prompt']}  \n"
        f"**Style:** {entry['style']} &nbsp;·&nbsp; "
        f"**Generated:** {entry['timestamp']}"
    )
    st.divider()

    _render_image_grid(recalled_images, key_prefix=f"gallery_{gallery_idx}")

    st.divider()
    if st.button("← Back to Generator", type="primary"):
        st.session_state["gallery_index"] = None
        st.rerun()
    st.stop()  # don't render the generator UI while in gallery view


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f'<p class="hero-title">{APP_TITLE}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="hero-sub">{APP_DESCRIPTION}</p>', unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.info(
        "💡 **Tip:** Add a `GROQ_API_KEY` to enable AI prompt refinement for better images. "
        "Get a free key at [console.groq.com/keys](https://console.groq.com/keys).",
        icon="🔑",
    )

st.divider()

# ── Controls ──────────────────────────────────────────────────────────────────
col_prompt, col_opts = st.columns([3, 2], gap="large")

with col_prompt:
    rnd_col, _ = st.columns([1, 3])
    with rnd_col:
        if st.button("🎲 Random Prompt", use_container_width=True):
            st.session_state["random_prompt"] = get_random_prompt()

    prompt_value = st.session_state.get("random_prompt", "")
    user_prompt: str = st.text_area(
        "✏️ Describe your image",
        value=prompt_value,
        placeholder="e.g. A futuristic Indian city at night with floating markets…",
        height=120,
    )

    negative_prompt: str = st.text_input(
        "🚫 Negative prompt (optional)",
        placeholder="e.g. blurry, low quality, distorted, watermark",
    )

with col_opts:
    style: str = st.radio("🎨 Style", STYLE_NAMES, horizontal=False)

    num_images: int = st.select_slider(
        "🖼️ Number of Images",
        options=[1, 2, 4],
        value=DEFAULT_NUM_IMAGES,
    )

st.divider()

# ── Generate Button ───────────────────────────────────────────────────────────
generate_btn = st.button("✨ Generate Images", type="primary", use_container_width=True)

if generate_btn:
    if not user_prompt.strip():
        st.warning("⚠️ Please enter a prompt before generating.", icon="⚠️")
        st.stop()

    # Build style-enhanced prompt
    enhanced_prompt, neg = build_prompt(user_prompt, style, negative_prompt)

    # Show prompt details
    groq_prompt = get_refined_prompt(enhanced_prompt, neg or None)
    with st.expander("🔍 See prompts", expanded=False):
        st.markdown("**Style-enhanced prompt:**")
        st.code(enhanced_prompt, language="text")
        if groq_prompt != enhanced_prompt:
            st.markdown("**✨ Groq-refined prompt (sent to image API):**")
            st.code(groq_prompt, language="text")
        if neg:
            st.markdown(f"**🚫 Negative prompt:** `{neg}`")

    # Generate
    with st.spinner("🎨 Generating your images… this may take 10–20 seconds"):
        try:
            images: List[Image.Image] = generate_images(
                prompt=enhanced_prompt,
                size=1024*1024,
                num_images=num_images,
                negative_prompt=neg or None,
            )
        except ImageGenerationError as exc:
            st.error(f"❌ {exc}", icon="🚨")
            st.stop()
        except Exception as exc:
            st.error(f"❌ Unexpected error: {exc}", icon="🚨")
            st.stop()

    # Save to history WITH images
    add_to_history(user_prompt, style, num_images, images=images)

    # Display
    st.success(f"✅ Generated {len(images)} image(s)! Saved to gallery →", icon="🎉")
    st.markdown("### 🖼️ Generated Images")
    _render_image_grid(images, key_prefix="new")

    st.session_state["random_prompt"] = ""
