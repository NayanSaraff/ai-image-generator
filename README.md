# 🎨 AI Image Generator — Powered by Groq

A production-ready, portfolio-grade Streamlit web application that transforms text descriptions into stunning AI-generated images using **Groq's ultra-fast LPU inference**. Choose from six artistic styles, tweak generation parameters, and download your results — all from a clean, dark-themed UI.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Groq-Powered** | Uses Groq's blazing-fast LPU inference for near-instant generation |
| **Style-Conditioned Prompts** | 6 styles: Realistic, Anime, Cyberpunk, Fantasy, Watercolor, 3D Render |
| **Image Size Selector** | 512×512 · 1024×1024 · 1024×1792 |
| **Multi-Image Generation** | Generate 1, 2, or 4 images per request in a responsive grid |
| **Negative Prompt** | Exclude unwanted elements from your image |
| **Random Prompt Generator** | One-click inspiration from 30+ curated creative prompts |
| **Prompt History** | Sidebar log of every generation (prompt, style, timestamp) |
| **Download Button** | Save any generated image as a PNG with one click |
| **Dark / Light Theme Toggle** | Switch themes without restarting the app |
| **Enhanced Prompt Preview** | See the full API prompt before it's sent |

---

## 🗂️ Project Structure

```
image_gen_chatbot/
├── app.py                     # Streamlit UI entry point
├── requirements.txt
├── README.md
├── .env.example               # API key template
├── .gitignore
│
├── config/
│   └── settings.py            # Env vars, constants, defaults
│
├── prompts/
│   └── styles.py              # Style templates & prompt builder
│
├── services/
│   └── image_generator.py     # Groq API image generation logic
│
├── utils/
│   ├── history.py             # Session-state history management
│   └── random_prompts.py      # Creative prompt bank (30+ prompts)
│
└── .streamlit/
    └── config.toml            # Dark violet theme & server config
```

---

## 🚀 Installation & Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/image-gen-chatbot.git
cd image-gen-chatbot
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your Groq API key

```bash
cp .env.example .env
```

Open `.env` and set your key:

```
GROQ_API_KEY=gsk_...
```

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 🔑 API Key Setup

This app uses **Groq** exclusively — only one key is needed.

### Get your free Groq API key

1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Sign in or create a free account
3. Click **Create API Key** and copy it
4. Paste it into your `.env` file:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **Note:** Groq has a generous free tier — no credit card required to start.

---

## ☁️ Deployment

### Streamlit Community Cloud *(Free)*

1. Push the repository to GitHub (ensure `.env` is listed in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo and set `app.py` as the entry point
4. Open **Advanced settings → Secrets** and add:

```toml
GROQ_API_KEY = "gsk_..."
```

5. Click **Deploy**

> Streamlit secrets are injected as environment variables at runtime — `python-dotenv` is only needed locally.

---

### Render *(Free tier available)*

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repository
3. Configure:

| Field | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

4. Under **Environment → Add Environment Variable** add `GROQ_API_KEY`
5. Click **Create Web Service**

---

## 🏛️ Architectural Decisions

### Why Groq?

Groq's LPU (Language Processing Unit) delivers inference speeds up to 10× faster than GPU-based providers. This means near-instant image generation feedback — a significantly better UX than waiting 15–30 seconds on traditional GPU APIs.

### Why a layered structure instead of one big file?

Separating `services/`, `prompts/`, `utils/`, and `config/` keeps each concern isolated. The Streamlit UI (`app.py`) contains zero API logic — swapping or upgrading the Groq model only requires a one-line change in `services/image_generator.py`.

### Why PIL/Pillow as the image layer?

Whether the API returns base64 or a URL, everything is normalised to a PIL `Image` before reaching the UI. This keeps rendering, downloading, and any future image processing uniform regardless of API response format.

### Why session state for history instead of a database?

For a portfolio demo, session state is zero-dependency and perfectly sufficient. Migrating to SQLite or PostgreSQL later only requires changes to `utils/history.py`.

---

## ⚠️ Known Limitations

- **Image generation model availability:** Groq's primary strength is text/code inference; their image generation endpoint is in active development. If the model identifier changes, update `GROQ_IMAGE_MODEL` in `config/settings.py`.
- **No persistent storage:** Prompt history lives in browser session state and resets on page refresh.
- **Negative prompt as suffix:** Groq's image API does not expose a separate `negative_prompt` field, so exclusions are appended to the positive prompt as `"Avoid: ..."`.
- **Rate limits:** Free-tier Groq accounts have per-minute request limits. The app surfaces these as friendly error messages.

---

## 📄 License

MIT — free to use, modify, and distribute.
