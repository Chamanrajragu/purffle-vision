<p align="center">
  <img src="https://img.shields.io/badge/Purffle_Studios-AI_Video_Creator-355C7D?style=for-the-badge&logo=youtube&logoColor=white" alt="PurffleVision"/>
</p>

<h1 align="center">PurffleVision — AI Video Creation Studio</h1>

<p align="center">
  <strong>Transform any topic into a cinematic video with AI — script, voiceover, visuals, and upload — all in one click.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/flask-web_app-000000?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenAI-GPT_3.5-412991?style=flat-square&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/MoviePy-video_engine-FF6F00?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
</p>

---

## What It Does

PurffleVision is a full-stack AI video creation platform built with Flask. Give it a topic, and it handles the entire pipeline:

1. **Script Generation** — GPT-3.5 writes an engaging video script tailored to your topic and language
2. **Voiceover Synthesis** — gTTS converts the script to natural-sounding speech in 50+ languages
3. **Visual Assembly** — Choose between AI-generated images (DALL-E) or stock video clips (Pexels)
4. **Video Compilation** — MoviePy stitches everything together with animated subtitles and transitions
5. **YouTube Upload** — One-click OAuth upload directly to your YouTube channel

## Features

- **Multi-language support** — Generate videos in any of 50+ languages supported by gTTS
- **Dual visual modes** — AI-generated imagery via DALL-E or curated stock footage from Pexels
- **Animated subtitles** — Auto-synced, fade-in/fade-out captions overlaid on every clip
- **YouTube integration** — OAuth 2.0 authentication and direct upload with custom metadata
- **Modern UI** — Clean, responsive Bootstrap 5 interface with Purffle Studios branding

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| AI | OpenAI GPT-3.5, DALL-E |
| TTS | Google Text-to-Speech (gTTS) |
| Video | MoviePy, ImageMagick |
| Stock Media | Pexels API |
| Upload | YouTube Data API v3 |
| Frontend | Bootstrap 5, Font Awesome |

## Quick Start

### Prerequisites

- Python 3.9+
- [ImageMagick](https://imagemagick.org/script/download.php) installed and on PATH
- API keys for OpenAI and Pexels
- Google OAuth credentials for YouTube upload (optional)

### Installation

```bash
# Clone the repo
git clone https://github.com/Chamanrajragu/purffle-vision.git
cd purffle-vision

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `PEXELS_API_KEY` | Your Pexels API key |
| `GOOGLE_CLIENT_SECRETS_FILE` | Path to Google OAuth credentials (default: `credentials.json`) |

## Project Structure

```
purffle-vision/
├── app.py                 # Flask application & video pipeline
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── templates/
│   └── index.html         # Main UI template
├── static/
│   └── brand/             # Purffle Studios assets
├── output_videos/         # Generated videos (gitignored)
├── ai_generated_images/   # DALL-E outputs (gitignored)
└── ai_generated_videos/   # AI video outputs (gitignored)
```

## Screenshots

<p align="center">
  <em>Modern, clean interface for creating AI-powered videos</em>
</p>

> Enter a topic → Choose your settings → Hit Generate → Watch your video come to life

---

<p align="center">
  Built with passion by <a href="https://github.com/Chamanrajragu"><strong>Purffle Studios</strong></a>
  <br/>
  <sub>Part of the Purffle ecosystem — PurffleTools · PurffleAI · Purffle.com</sub>
</p>
