"""
AI Image Generation Chatbot — main Streamlit entry point.

Layout:
  Sidebar  → branding, stats, quick gallery strip
  Tab 1    → Generate (prompt + controls + results)
  Tab 2    → Gallery  (full session image history)
  Tab 3    → Settings (theme, API status)
"""

from __future__ import annotations

import io
import time
from typing import List, Optional

import streamlit as st
from PIL import Image

from config.settings import (
    APP_DESCRIPTION,
    APP_TITLE,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_NUM_IMAGES,
    IMAGE_SIZES,
    GROQ_API_KEY,
)
from prompts.styles import STYLE_NAMES, build_prompt
from services.image_generator import (
    ImageGenerationError,
    generate_images,
    get_refined_prompt,
)
from utils.history import (
    add_to_history,
    bytes_to_images,
    clear_history,
    get_history,
    init_history,
)
from utils.random_prompts import get_random_prompt

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
init_history()
for key, default in [
    ("theme", "Dark"),
    ("random_prompt", ""),
    ("last_images", []),
    ("last_prompt", ""),
    ("last_style", ""),
    ("seed", 42),
    ("lock_seed", False),
    ("active_tab", "Generate"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── CSS ───────────────────────────────────────────────────────────────────────
def _css(theme: str) -> None:
    bg     = "#0F0F1A" if theme == "Dark" else "#F8F9FB"
    card   = "#1A1A2E" if theme == "Dark" else "#FFFFFF"
    text   = "#E2E8F0" if theme == "Dark" else "#1A1A2E"
    muted  = "#94A3B8" if theme == "Dark" else "#64748B"
    border = "#2D2D4E" if theme == "Dark" else "#E2E8F0"

    st.markdown(f"""
    <style>
    /* ── Base ── */
    .stApp {{ background-color: {bg}; color: {text}; }}
    section[data-testid="stSidebar"] {{ background-color: {card}; border-right: 1px solid {border}; }}

    /* ── Brand header ── */
    .brand {{ display:flex; align-items:center; gap:12px; padding:1rem 0 0.5rem; }}
    .brand-icon {{ font-size:2.2rem; }}
    .brand-name {{ font-size:1.5rem; font-weight:800; letter-spacing:-0.5px; color:{text}; }}
    .brand-sub  {{ font-size:0.75rem; color:{muted}; margin-top:-2px; }}

    /* ── Stat pills ── */
    .stats {{ display:flex; gap:8px; flex-wrap:wrap; margin:0.75rem 0; }}
    .stat-pill {{
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.72rem;
        color: {text};
    }}

    /* ── Section headers ── */
    .section-label {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: {muted};
        margin: 1rem 0 0.4rem;
    }}

    /* ── Control card ── */
    .ctrl-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }}

    /* ── Generate button ── */
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, #7C3AED, #4F46E5);
        border: none;
        border-radius: 10px;
        font-size: 1.05rem;
        font-weight: 700;
        padding: 0.65rem 1rem;
        letter-spacing: 0.3px;
        transition: opacity 0.2s;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{ opacity: 0.88; }}
    div[data-testid="stButton"] > button {{ border-radius: 8px; font-weight: 600; }}

    /* ── Image card ── */
    .img-wrap {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 0.75rem;
    }}
    .img-meta {{
        padding: 0.5rem 0.75rem;
        font-size: 0.72rem;
        color: {muted};
    }}

    /* ── Gallery thumb ── */
    .gallery-entry {{
        background: {card};
        border: 1px solid {border};
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 0.6rem;
    }}
    .gallery-meta {{
        padding: 0.45rem 0.65rem;
        font-size: 0.7rem;
        color: {muted};
        line-height: 1.5;
    }}
    .gallery-prompt {{
        font-weight: 600;
        color: {text};
        font-size: 0.78rem;
    }}

    /* ── Status badge ── */
    .badge-ok  {{ color:#22C55E; font-weight:700; font-size:0.78rem; }}
    .badge-off {{ color:#F59E0B; font-weight:700; font-size:0.78rem; }}

    /* ── Prompt expander ── */
    .prompt-box {{
        background: rgba(124,58,237,0.08);
        border-left: 3px solid #7C3AED;
        border-radius: 0 8px 8px 0;
        padding: 0.6rem 0.9rem;
        font-size: 0.82rem;
        color: {text};
        margin: 0.3rem 0;
        word-break: break-word;
    }}

    /* ── Result header ── */
    .result-header {{
        font-size: 1.15rem;
        font-weight: 700;
        margin: 1rem 0 0.6rem;
        color: {text};
    }}

    /* hide default streamlit header chrome */
    #MainMenu, footer {{ visibility:hidden; }}

    
    </style>
    """, unsafe_allow_html=True)


_css(st.session_state["theme"])


# ── Utilities ─────────────────────────────────────────────────────────────────
def _img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _thumb(img_bytes: bytes, size: int = 280) -> Image.Image:
    img = Image.open(io.BytesIO(img_bytes))
    img.thumbnail((size, size))
    return img

def _prompt_to_filename(prompt: str, idx: int, style: str = "") -> str:
    """Generate a meaningful filename from the prompt text."""
    import re
    # Take first 5 words, lowercase, remove special chars
    words = prompt.strip().lower().split()[:5]
    slug = "_".join(re.sub(r"[^a-z0-9]", "", w) for w in words if w)
    slug = slug[:40]  # cap length
    style_tag = style.lower().replace(" ", "_") if style else ""
    return f"{style_tag}_{slug}_{idx + 1}.png" if style_tag else f"{slug}_{idx + 1}.png"

def _render_image_grid(
    images: List[Image.Image],
    key_prefix: str = "img",
    prompt: str = "",
    style: str = "",
) -> None:
    """Render images in a 1- or 2-column grid with metadata and download."""
    ncols = 1 if len(images) == 1 else 2
    cols = st.columns(ncols, gap="medium")
    for idx, img in enumerate(images):
        with cols[idx % ncols]:
            st.markdown('<div class="img-wrap">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown(
                f'<div class="img-meta">🎨 {style} &nbsp;·&nbsp; 📐 {img.size[0]}×{img.size[1]}px</div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button(
                label=f"⬇️ Download #{idx + 1}",
                data=_img_to_bytes(img),
                file_name=_prompt_to_filename(prompt, idx, style),
                mime="image/png",
                use_container_width=True,
                key=f"{key_prefix}_dl_{idx}_{int(time.time())}",
            )


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎨</div>
        <div>
            <div class="brand-name">ImageGen AI</div>
            <div class="brand-sub">Groq · Pollinations.ai</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    history = get_history()
    total_images = sum(e.get("num_images", 0) for e in history)
    st.markdown(f"""
    <div class="stats">
        <span class="stat-pill">🖼️ {total_images} images</span>
        <span class="stat-pill">📋 {len(history)} prompts</span>
        <span class="stat-pill">{'🟢 Groq on' if GROQ_API_KEY else '🟡 No Groq'}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Recent generations strip
    if history:
        st.markdown('<div class="section-label">Recent</div>', unsafe_allow_html=True)
        for i, entry in enumerate(history[:4]):
            if entry.get("image_bytes"):
                thumb = _thumb(entry["image_bytes"][0], size=240)
                st.image(thumb, use_container_width=True, caption=entry["prompt"][:40] + "…")
        if len(history) > 4:
            st.caption(f"+ {len(history) - 4} more in Gallery tab")
    else:
        st.info("Generate your first image to see it here.", icon="💡")


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_generate, tab_gallery, tab_settings = st.tabs([
    "✨ Generate",
    f"🖼️ Gallery ({len(history)})",
    "⚙️ Settings",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — GENERATE
# ═════════════════════════════════════════════════════════════════════════════
with tab_generate:

    # ── Two-column layout: LEFT = prompt area, RIGHT = controls panel ─────────
    col_left, col_right = st.columns([3, 2], gap="large")

    # ── LEFT: Prompt area ─────────────────────────────────────────────────────
    with col_left:
        st.markdown('<div class="section-label">Your Prompt</div>', unsafe_allow_html=True)

        # Random prompt + prompt input on same row
        r1, r2 = st.columns([1, 4])
        with r1:
            if st.button("🎲 Random", use_container_width=True, help="Fill with a random creative prompt"):
                st.session_state["random_prompt"] = get_random_prompt()
                st.rerun()

        prompt_val = st.session_state.get("random_prompt", "")
        user_prompt: str = st.text_area(
            "Describe your image",
            value=prompt_val,
            placeholder="e.g. A futuristic Indian city at night with glowing neon floating markets…",
            height=130,
            label_visibility="collapsed",
        )

        negative_prompt: str = st.text_input(
            "🚫 Negative prompt",
            placeholder="blurry, low quality, distorted, watermark, text",
            help="Describe what you DON'T want in the image",
        )

        # Seed control
        st.markdown('<div class="section-label">Seed Control</div>', unsafe_allow_html=True)
        s1, s2 = st.columns([3, 2])
        with s1:
            seed_val: int = st.number_input(
                "Seed",
                min_value=0,
                max_value=999999,
                value=st.session_state["seed"],
                step=1,
                label_visibility="collapsed",
                help="Same seed + same prompt = same image. Change seed for variety.",
            )
        with s2:
            lock_seed: bool = st.toggle(
                "🔒 Lock seed",
                value=st.session_state["lock_seed"],
                help="Lock to reproduce the exact same image",
            )
        st.session_state["seed"] = seed_val
        st.session_state["lock_seed"] = lock_seed

        if lock_seed:
            st.caption(f"🔒 Seed locked at **{seed_val}** — same prompt will reproduce the same image.")
        else:
            st.caption("🎲 Seed auto-changes each run for variety.")

    # ── RIGHT: Controls panel ─────────────────────────────────────────────────
    with col_right:
        st.markdown('<div class="section-label">Style</div>', unsafe_allow_html=True)
        style: str = st.radio(
            "Style",
            STYLE_NAMES,
            horizontal=False,
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-label">Output Settings</div>', unsafe_allow_html=True)

        # Size options with human-readable labels
        SIZE_LABELS = {
            "512x512":   "512×512 — Small / Fast",
            "768x768":   "768×768 — Medium Square",
            "1024x1024": "1024×1024 — Large Square ⭐",
            "1280x720":  "1280×720 — Landscape 16:9",
            "1024x1792": "1024×1792 — Portrait 9:16",
            "1920x1080": "1920×1080 — Full HD",
        }
        size_label = st.selectbox(
            "📐 Size",
            options=IMAGE_SIZES,
            index=IMAGE_SIZES.index(DEFAULT_IMAGE_SIZE),
            format_func=lambda s: SIZE_LABELS.get(s, s),
            help="Choose the output image dimensions",
        )
        image_size: str = size_label

        num_images: int = st.select_slider(
            "🖼️ Count",
            options=[1, 2, 4],
            value=DEFAULT_NUM_IMAGES,
        )

        st.markdown("")
        _, btn_col, _ = st.columns([1, 4, 1])
        with btn_col:
            generate_btn = st.button(
                "✨ Generate Images",
                type="primary",
                use_container_width=True,
            )
        if st.session_state["last_prompt"]:
            st.caption(f"Last: *{st.session_state['last_prompt'][:50]}…*")

    

    st.divider()
    # ── Generation logic ──────────────────────────────────────────────────────
    if generate_btn:
        if not user_prompt.strip():
            st.warning("⚠️ Please enter a prompt first.", icon="⚠️")
            st.stop()

        # Build prompts
        enhanced_prompt, neg = build_prompt(user_prompt, style, negative_prompt)
        groq_prompt = get_refined_prompt(enhanced_prompt, neg or None)

        # Show prompt pipeline
        with st.expander("🔍 Prompt pipeline", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Style-enhanced**")
                st.markdown(f'<div class="prompt-box">{enhanced_prompt}</div>', unsafe_allow_html=True)
            with c2:
                if groq_prompt != enhanced_prompt:
                    st.markdown("**✨ Groq-refined**")
                    st.markdown(f'<div class="prompt-box">{groq_prompt}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("**Groq refinement**")
                    st.info("Add GROQ_API_KEY to enable prompt refinement.", icon="💡")
            if neg:
                st.markdown(f"**🚫 Negative:** `{neg}`")

        # Resolve seed
        current_seed = seed_val if lock_seed else int(time.time()) % 999999

        # Generate
        progress = st.progress(0, text="🎨 Starting generation…")
        try:
            progress.progress(20, text="🔄 Refining prompt with Groq…" if GROQ_API_KEY else "🔄 Building prompt…")
            images: List[Image.Image] = generate_images(
                prompt=enhanced_prompt,
                size=image_size,
                num_images=num_images,
                negative_prompt=neg or None,
                seed=current_seed,
            )
            progress.progress(100, text="✅ Done!")
            time.sleep(0.4)
            progress.empty()
        except ImageGenerationError as exc:
            progress.empty()
            st.error(f"❌ {exc}", icon="🚨")
            st.stop()
        except Exception as exc:
            progress.empty()
            st.error(f"❌ Unexpected error: {exc}", icon="🚨")
            st.stop()

        # Save to history
        add_to_history(user_prompt, style, num_images, images=images)
        st.session_state["last_images"] = images
        st.session_state["last_prompt"] = user_prompt
        st.session_state["last_style"]  = style
        st.session_state["random_prompt"] = ""
        if not lock_seed:
            st.session_state["seed"] = current_seed

        # Results
        st.markdown(
            f'<div class="result-header">🖼️ Generated {len(images)} image{"s" if len(images) > 1 else ""}</div>',
            unsafe_allow_html=True,
        )
        _render_image_grid(images, key_prefix="gen", prompt=user_prompt, style=style)
        st.success("✅ Saved to Gallery tab!", icon="🎉")

    # ── Show last result if no new generation ─────────────────────────────────
    elif st.session_state["last_images"] and not generate_btn:
        st.markdown('<div class="result-header">🖼️ Last Generated Images</div>', unsafe_allow_html=True)
        _render_image_grid(
            st.session_state["last_images"],
            key_prefix="last",
            prompt=st.session_state["last_prompt"],
            style=st.session_state["last_style"],
        )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — GALLERY
# ═════════════════════════════════════════════════════════════════════════════
with tab_gallery:
    history = get_history()

    if not history:
        st.markdown("### 🖼️ Your Gallery")
        st.info("No images yet. Head to the Generate tab to create some!", icon="🎨")
    else:
        # Header row
        h1, h2 = st.columns([4, 1])
        with h1:
            st.markdown(f"### 🖼️ Gallery — {len(history)} generation{'s' if len(history) > 1 else ''}")
        with h2:
            if st.button("🗑️ Clear All", use_container_width=True):
                clear_history()
                st.session_state["last_images"] = []
                st.rerun()

        st.divider()

        # Render each history entry
        for i, entry in enumerate(history):
            has_images = bool(entry.get("image_bytes"))

            with st.expander(
                f"🎨 {entry['style']}  ·  {entry['prompt'][:70]}{'…' if len(entry['prompt']) > 70 else ''}  ·  {entry['timestamp']}",
                expanded=(i == 0),  # expand the most recent
            ):
                if has_images:
                    recalled = bytes_to_images(entry["image_bytes"])
                    ncols = 1 if len(recalled) == 1 else 2
                    cols = st.columns(ncols, gap="medium")
                    for j, img in enumerate(recalled):
                        with cols[j % ncols]:
                            st.image(img, use_container_width=True)
                            st.download_button(
                                label=f"⬇️ Download #{j + 1}",
                                data=_img_to_bytes(img),
                                file_name=_prompt_to_filename(entry["prompt"], j, entry["style"]),
                                mime="image/png",
                                use_container_width=True,
                                key=f"gal_dl_{i}_{j}",
                            )

                    st.markdown(
                        f"**Full prompt:** {entry['prompt']}  \n"
                        f"**Style:** {entry['style']} &nbsp;·&nbsp; "
                        f"**Images:** {entry['num_images']} &nbsp;·&nbsp; "
                        f"**Generated:** {entry['timestamp']}"
                    )
                else:
                    st.warning("Images not available for this entry.")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
with tab_settings:
    st.markdown("### ⚙️ Settings")

    s1, s2 = st.columns(2, gap="large")

    with s1:
        # Theme
        st.markdown('<div class="section-label">Appearance</div>', unsafe_allow_html=True)
        theme_choice = st.radio(
            "Theme",
            ["Dark", "Light"],
            index=0 if st.session_state["theme"] == "Dark" else 1,
            horizontal=True,
        )
        if theme_choice != st.session_state["theme"]:
            st.session_state["theme"] = theme_choice
            st.rerun()

        st.divider()

        # Session stats
        st.markdown('<div class="section-label">Session Stats</div>', unsafe_allow_html=True)
        history = get_history()
        total_imgs = sum(e.get("num_images", 0) for e in history)
        styles_used = list(dict.fromkeys(e["style"] for e in history))

        st.markdown(f"- **Total generations:** {len(history)}")
        st.markdown(f"- **Total images:** {total_imgs}")
        st.markdown(f"- **Styles used:** {', '.join(styles_used) if styles_used else 'None yet'}")

    with s2:
        # API Status
        st.markdown('<div class="section-label">API Status</div>', unsafe_allow_html=True)

        groq_status = (
            '<span class="badge-ok">● Connected</span>' if GROQ_API_KEY
            else '<span class="badge-off">● Not configured</span>'
        )
        st.markdown(f"""
        | Service | Status |
        |---|---|
        | Groq (prompt refinement) | {groq_status} |
        | Pollinations.ai (images) | <span class="badge-ok">● Always available</span> |
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown('<div class="section-label">Add Groq Key</div>', unsafe_allow_html=True)
        if not GROQ_API_KEY:
            st.markdown(
                "Add `GROQ_API_KEY` to your `.env` file to enable AI prompt refinement.  \n"
                "Get a free key → [console.groq.com/keys](https://console.groq.com/keys)"
            )
        else:
            st.success("Groq is active. Prompts are being AI-refined before generation.", icon="✅")

        st.divider()

        st.markdown('<div class="section-label">About</div>', unsafe_allow_html=True)
        st.markdown(
            "**Stack:** Streamlit · Groq · Pollinations.ai · FLUX.1  \n"
            "**Image model:** FLUX.1-schnell via Pollinations  \n"
            "**Prompt model:** llama-3.3-70b-versatile via Groq  \n"
        )
