<div align="center">

# PurffleVision — AI Video Creation Studio

**Generate professional YouTube videos from a single topic using AI-powered scripts, voiceovers, stock footage, and automated editing.**

[![Python](https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-web_app-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)

[Features](#-features) · [Screenshots](#-screenshots) · [Quick Start](#-quick-start) · [How It Works](#-how-it-works) · [Tech Stack](#%EF%B8%8F-tech-stack)

</div>

<div align="center">

### ⭐ Star this repo if you find it useful — it really helps! &nbsp;·&nbsp; 🌐 [**Live page → purffle.com/purffle-vision**](https://purffle.com/purffle-vision/)

</div>


---

## 📸 Screenshots

<div align="center">

![PurffleVision Dashboard](screenshots/dashboard.png)

*Dark-themed UI with glass morphism design, animated gradient orbs, and a 5-step video generation pipeline*

</div>

---

## 🎬 What is PurffleVision?

PurffleVision is an **AI-powered video creation platform** that turns any topic into a fully produced video. Built with Python and Flask, it automates the entire video production workflow — from scriptwriting to final render.

Ideal for **content creators**, **YouTubers**, **digital marketers**, and anyone who wants to produce professional video content at scale without manual editing.

---

## 🔄 How It Works

```
Topic → AI Script → Voice Synthesis → Stock Footage / AI Images → Video Assembly → Export / Upload
```

| Step | What Happens | Technology |
|------|-------------|------------|
| 1. **Script** | GPT writes an engaging, retention-optimized video script | OpenAI API |
| 2. **Voiceover** | Text-to-speech in 50+ languages | Google TTS (gTTS) |
| 3. **Visuals** | Fetches matching stock videos or generates AI images | Pexels API / DALL-E |
| 4. **Assembly** | Composites footage, adds subtitles, overlays audio | MoviePy + ImageMagick |
| 5. **Export** | Renders final MP4, optional direct YouTube upload | YouTube Data API v3 |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **One-click generation** | Enter a topic, click Generate, get a complete video |
| **50+ languages** | Voiceovers in English, Spanish, Hindi, Japanese, and more |
| **Dual visual modes** | Stock footage (Pexels) or AI-generated images (DALL-E) |
| **Animated subtitles** | Word-wrapped, fade-animated captions synced to voiceover |
| **YouTube upload** | OAuth 2.0 integration for direct channel publishing |
| **Modern dark UI** | Glass morphism cards, animated orbs, responsive design |
| **Smart validation** | Clear error messages when API keys aren't configured |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [ImageMagick](https://imagemagick.org/script/download.php) installed
- API keys: [OpenAI](https://platform.openai.com/api-keys) + [Pexels](https://www.pexels.com/api/)

### Install & Run

```bash
# Clone
git clone https://github.com/Chamanrajragu/purffle-vision.git
cd purffle-vision

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env → add your OPENAI_API_KEY and PEXELS_API_KEY

# Run
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for script generation + DALL-E |
| `PEXELS_API_KEY` | ✅ | Pexels API key for stock video footage |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.9+, Flask |
| **AI Engine** | OpenAI GPT, DALL-E |
| **Voice** | Google Text-to-Speech (gTTS) |
| **Video** | MoviePy, ImageMagick, Pillow |
| **Media** | Pexels API |
| **Upload** | YouTube Data API v3, Google OAuth 2.0 |
| **Frontend** | Custom CSS, Inter font, glass morphism |

---

## 📁 Project Structure

```
purffle-vision/
├── app.py                 # Flask app + video generation pipeline
├── templates/
│   └── index.html         # Modern dark-themed UI
├── static/
│   ├── uploads/           # Generated videos served here
│   └── brand/             # Purffle branding assets
├── screenshots/           # README screenshots
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
└── output_videos/         # Raw generated videos
```

---

## ⚠️ Disclaimer

> This is an open-source video creation tool for educational and creative purposes. Requires your own API keys. AI-generated content should be reviewed before publishing. Not affiliated with YouTube, OpenAI, or Pexels.

---

<div align="center">

**Built by [Chaman Raj](https://github.com/Chamanrajragu)**

Part of the **Purffle** ecosystem — PurffleTools · PurffleAI · [Purffle.com](https://purffle.com)

</div>


---

<!-- purffle-ecosystem -->
## 🧩 The Purffle toolset

**PurffleVision** is part of **[Purffle](https://purffle.com)** — a growing set of free, open-source tools built in the open. **If this saved you time, please drop a ⭐ — it genuinely helps the project reach more people!**

| Tool | What it does |
|------|--------------|
| 🔄 **[Claude Multi](https://purffle.com/claude-multi/)** | Run Claude Code with multiple accounts — auto-switch on the 5-hour limit · paid app, from $5/month |
| 📐 **[Purffle Chartwright](https://purffle.com/purffle-chartwright/)** | Desktop chart analysis where the AI cannot invent a price |
| 🎵 **[PurffleGrab](https://github.com/Chamanrajragu/purffle-grab)** | Free Spotify & YouTube downloader — MP3, MP4, 4K |
| 🎥 **[PurffleVision](https://github.com/Chamanrajragu/purffle-vision)** 👈 | AI video creation — any topic to a finished video |
| ⚡ **[PurffleShorts](https://github.com/Chamanrajragu/purffle-shorts)** | Autonomous YouTube Shorts generator |
| 📈 **[PurffleTrader](https://github.com/Chamanrajragu/purffle-trader)** | Crypto paper-trading bot — Binance, EMA + RSI |
| 🤖 **[PurffleCopyBot](https://github.com/Chamanrajragu/purffle-copybot)** | Copy-trading bot — mirror top Hyperliquid traders |

<sub>🌐 [purffle.com](https://purffle.com) · 💼 by [Chaman Raj](https://github.com/Chamanrajragu) · ⭐ Star to support open-source</sub>

<sub>Keywords: ai video generator, text to video, automated youtube videos, gpt video maker, faceless youtube</sub>

---

## Need Something Like This Built for You?

I wrote this. I also write Python for other people — fixed price, agreed before I start.

- **Python automation** — batch file processing, Excel/CSV cleaning, API pulls, scheduled reports, packaged as a `.exe` if you do not use Python · *1–5 days*
- **Web scraping** — clean data as Excel, CSV, JSON or Sheets, plus the reusable scraper · *1–4 days*
- **Custom AI chatbots** — trained on your own docs, full source code, no monthly fee · *2–7 days*
- **Excel and Google Sheets** — formulas, dashboards, macros, Apps Script · *1–4 days*

I only take work I can verify myself before delivering it — I run it on your real data first.

[![Hire me on Fiverr](https://img.shields.io/badge/Hire_me_on_Fiverr-1DBF73?style=for-the-badge&logo=fiverr&logoColor=white)](https://www.fiverr.com/purffle)
[![Email](https://img.shields.io/badge/info@purffle.com-d97757?style=for-the-badge&logo=maildotru&logoColor=white)](mailto:info@purffle.com)

More of what I have built: [purffle.com](https://purffle.com) · [purffle.tools](https://purffle.tools) · [purffleai.com](https://purffleai.com) · [purfflestudios.com](https://purfflestudios.com)
