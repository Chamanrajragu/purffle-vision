import os
import re
import logging
import pickle
import requests
import shutil
import uuid
import threading

from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
from gtts import gTTS
from gtts.lang import tts_langs
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    ImageClip,
    TextClip,
    CompositeVideoClip
)
from moviepy.config import change_settings
try:
    from moviepy.video.fx.crop import crop as _mpy_crop
except Exception:  # pragma: no cover - older/newer moviepy layouts
    _mpy_crop = None
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import openai

# --------------------------------------------------------------------------------
# Flask App Config
# --------------------------------------------------------------------------------
app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --------------------------------------------------------------------------------
# ImageMagick Configuration (Auto-Detect + Fallback)
# --------------------------------------------------------------------------------
# Try to detect magick.exe automatically or use fallback path
im_path = shutil.which("magick") or r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

if os.path.exists(im_path):
    change_settings({"IMAGEMAGICK_BINARY": im_path})
    logging.info(f"ImageMagick successfully linked: {im_path}")
else:
    logging.warning(f"ImageMagick not found at {im_path} — video generation with text overlays will not work until installed.")

# --------------------------------------------------------------------------------
# API Keys
# --------------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --------------------------------------------------------------------------------
# Directory Configurations
# --------------------------------------------------------------------------------
BACKGROUND_VIDEO_FOLDER = "background_videos/"
OUTPUT_FOLDER = "output_videos/"
AI_IMAGES_FOLDER = "ai_generated_images/"
AI_VIDEOS_FOLDER = "ai_generated_videos/"
UPLOADS_FOLDER = "static/uploads/"

# Ensure all necessary directories exist
for folder in [
    BACKGROUND_VIDEO_FOLDER,
    OUTPUT_FOLDER,
    AI_IMAGES_FOLDER,
    AI_VIDEOS_FOLDER,
    UPLOADS_FOLDER
]:
    os.makedirs(folder, exist_ok=True)

# --------------------------------------------------------------------------------
# YouTube API Scopes
# --------------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


# --------------------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------------------

def sanitize_filename(name):
    """
    Sanitizes the input string to create safe filenames.
    Replaces invalid characters with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)


# Aspect ratio presets -> (width, height) target. 16:9 keeps native (no transform).
ASPECT_PRESETS = {
    "16:9": None,            # landscape — leave clips as-is (default, safest)
    "9:16": (720, 1280),     # vertical — Shorts / Reels / TikTok
    "1:1": (1080, 1080),     # square — feed posts
}
ASPECT_ORIENTATION = {"16:9": "landscape", "9:16": "portrait", "1:1": "square"}


def fit_to_aspect(clip, size):
    """Resize-to-cover then center-crop `clip` to `size`=(w,h). Safe: returns the
    original clip unchanged if no size is given or anything goes wrong, so a crop
    issue can never break video generation."""
    if not size or _mpy_crop is None:
        return clip
    tw, th = size
    try:
        scale = max(tw / clip.w, th / clip.h)
        resized = clip.resize(scale)
        return _mpy_crop(resized, x_center=resized.w / 2, y_center=resized.h / 2,
                         width=tw, height=th)
    except Exception as e:
        logging.error(f"Aspect fit to {size} failed, using original framing: {e}")
        return clip

def authenticate_youtube():
    """
    Authenticates the application with YouTube using OAuth 2.0.
    Returns a YouTube service object.
    """
    creds = None
    token_path = "token.pickle"
    try:
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "credentials.json"), SCOPES
                )
                creds = flow.run_local_server(port=8080)

            with open(token_path, "wb") as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        raise

def generate_text_content(prompt, length=150):
    """
    Generates text content using OpenAI's ChatCompletion API.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"].strip()
        else:
            logging.error("No valid choices found in the OpenAI response.")
            return "Default script content due to an error."
    except Exception as e:
        logging.error(f"Error generating script: {e}")
        return "Default script content due to an error."

def generate_voiceover(text, output_path, language="en"):
    """
    Generates a voiceover using gTTS.
    """
    try:
        supported_langs = tts_langs()
        if language not in supported_langs:
            logging.warning(f"Language '{language}' not supported. Falling back to English.")
            language = "en"
        tts = gTTS(text=text, lang=language)
        tts.save(output_path)
        logging.info(f"Voiceover generated using gTTS in language '{language}'.")
    except Exception as e:
        logging.error(f"Error generating voiceover with gTTS: {e}")
        raise

def generate_ai_images(topic, num_images=10):
    """
    Generates AI images related to the given topic using OpenAI's Image API.
    """
    images = []
    for i in range(num_images):
        prompt = f"Create an aesthetically pleasing and detailed image related to {topic}."
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512"
            )
            image_url = response["data"][0]["url"]
            image_path = os.path.join(AI_IMAGES_FOLDER, f"{sanitize_filename(topic)}_image_{i}.png")

            # Download the generated image
            with open(image_path, "wb") as file:
                file.write(requests.get(image_url).content)

            images.append(image_path)
            logging.info(f"Generated image {i + 1} for topic '{topic}'.")
        except Exception as e:
            logging.error(f"Error generating image {i + 1} for topic '{topic}': {e}")
    return images

def create_video_from_images(images, voiceover_path, output_path, subtitles, target_size=None):
    """
    Creates a slideshow-style video by stitching images together and synchronizing with the voiceover.
    Each image is displayed for an equal share of the voiceover duration.
    `target_size` (w, h) optionally reframes each image to a chosen aspect ratio.
    """
    try:
        # Load the audio clip to get its duration
        audio_clip = AudioFileClip(voiceover_path)
        audio_duration = audio_clip.duration
        logging.info(f"Voiceover duration: {audio_duration} seconds.")

        # Spread all images evenly across the voiceover (decoupled from subtitle count
        # so every generated image is used). Captions are optional.
        num_images = len(images)
        image_duration = audio_duration / num_images if num_images > 0 else 4

        clips = []
        for i, img in enumerate(images):
            img_clip = fit_to_aspect(ImageClip(img).set_duration(image_duration), target_size)

            subtitle = subtitles[i] if i < len(subtitles) else ""
            if subtitle:
                text_clip = (TextClip(
                    subtitle,
                    fontsize=24,
                    color="white",
                    stroke_color="black",
                    stroke_width=1,
                    bg_color="transparent",
                    size=(img_clip.w, None),
                    method="caption"
                )
                .set_position(("center", "bottom"))
                .set_duration(image_duration)
                .fadein(0.3)
                .fadeout(0.3))
                clips.append(CompositeVideoClip([img_clip, text_clip]))
            else:
                clips.append(img_clip)

        final_clip = concatenate_videoclips(clips, method="compose")
        final_video = final_clip.set_audio(audio_clip).set_duration(audio_duration)

        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

        logging.info(f"AI-generated video with subtitles created successfully: {output_path}")

        # Close clips
        final_clip.close()
        audio_clip.close()
        for c in clips:
            c.close()

        return output_path
    except Exception as e:
        logging.error(f"Error creating AI-generated video with subtitles: {e}")
        return None

# --------------------------------------------------------------------------------
# New Pexels Function with Animated Subtitles
# --------------------------------------------------------------------------------

def fetch_pexels_videos(topic, max_clips=3, orientation="landscape"):
    """
    Searches Pexels for multiple short videos and downloads them locally.
    Returns a list of local paths to the downloaded files.
    """
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "query": topic,
        "orientation": orientation,
        "per_page": max_clips
    }

    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        logging.error(f"Error fetching videos from Pexels: {resp.status_code}")
        return []

    data = resp.json()
    if "videos" not in data or len(data["videos"]) == 0:
        logging.warning(f"No videos found for topic '{topic}'.")
        return []

    downloaded_paths = []
    for i, video_item in enumerate(data["videos"]):
        video_files = video_item.get("video_files", [])
        if not video_files:
            continue

        # Grab the first file or choose a suitable resolution
        file_link = video_files[0]["link"]
        local_path = os.path.join(UPLOADS_FOLDER, f"{sanitize_filename(topic)}_{i}.mp4")

        try:
            content = requests.get(file_link).content
            with open(local_path, "wb") as f:
                f.write(content)

            logging.info(f"Downloaded clip {i+1} to: {local_path}")
            downloaded_paths.append(local_path)
        except Exception as e:
            logging.error(f"Failed to download {file_link}: {e}")

    return downloaded_paths

def create_video_from_pexels_clips_with_subtitles(topic, voiceover_path, output_path,
                                                  subtitles, max_clips=3,
                                                  target_size=None, orientation="landscape"):
    """
    1. Fetch multiple short Pexels video clips for 'topic'.
    2. Concatenate them.
    3. Loop or trim to match the exact voiceover duration.
    4. Overlay the voiceover.
    5. Add animated subtitles that fade in/out in sync with each subtitle's time slot.
    6. Save final video to 'output_path'.
    `target_size` (w, h) optionally reframes the montage to a chosen aspect ratio.
    """
    # --- 1) Download multiple short clips from Pexels ---
    video_paths = fetch_pexels_videos(topic, max_clips=max_clips, orientation=orientation)
    if not video_paths:
        logging.error("No Pexels video clips were downloaded.")
        return None

    # --- 2) Concatenate them ---
    clips = []
    for vp in video_paths:
        try:
            clip = VideoFileClip(vp)
            clips.append(clip)
        except Exception as e:
            logging.error(f"Error loading clip {vp}: {e}")
    if not clips:
        logging.error("No valid video clips to combine.")
        return None

    combined_clip = concatenate_videoclips(clips, method="compose")

    # --- 3) Match total duration to the voiceover ---
    audio_clip = AudioFileClip(voiceover_path)
    audio_duration = audio_clip.duration

    # Trim or loop to match the voiceover length
    if combined_clip.duration > audio_duration:
        combined_clip = combined_clip.subclip(0, audio_duration)
    elif combined_clip.duration < audio_duration:
        final_clips = []
        current_duration = 0.0
        while current_duration < audio_duration:
            final_clips.append(combined_clip.copy())
            current_duration += combined_clip.duration
        extended_clip = concatenate_videoclips(final_clips, method="compose")
        combined_clip = extended_clip.subclip(0, audio_duration)

    # --- 3b) Reframe to the requested aspect ratio (vertical/square) if any ---
    combined_clip = fit_to_aspect(combined_clip, target_size)

    # --- 4) Overlay the voiceover (no subtitles yet) ---
    final_clip_no_subs = combined_clip.set_audio(audio_clip)

    # --- 5) Add animated subtitles ---
    num_subs = len(subtitles)
    if num_subs == 0:
        # If no subtitles, just use the final clip with voiceover
        final_clip = final_clip_no_subs
    else:
        sub_duration = audio_duration / num_subs

        # Build sub-clips: each sub-clip shows one line of text for sub_duration
        sub_clips = []
        for i, line in enumerate(subtitles):
            start_t = i * sub_duration
            end_t = start_t + sub_duration

            # Readable captions: white text with a black outline (stroke). We avoid an
            # rgba() bg_color here because many ImageMagick builds reject it and abort
            # the whole render — a transparent background + stroke is portable.
            txt_clip = (TextClip(
                line,
                fontsize=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                size=(combined_clip.w, None),
                method='caption',
                align='center',
                bg_color='transparent'
            )
            .set_position(('center', 'bottom'))
            .set_start(start_t)
            .set_duration(sub_duration)
            .fadein(0.5)
            .fadeout(0.5))

            sub_clips.append(txt_clip)

        # Overlay subtitles on top of the final_clip_no_subs
        final_clip = CompositeVideoClip([final_clip_no_subs, *sub_clips], size=combined_clip.size)

    # --- 6) Save final video to 'output_path' ---
    final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    logging.info(f"Final Pexels-based video with subtitles saved at: {output_path}")

    # Cleanup
    final_clip.close()
    audio_clip.close()
    combined_clip.close()
    for c in clips:
        c.close()

    return output_path


# --------------------------------------------------------------------------------
# YouTube Upload
# --------------------------------------------------------------------------------

def upload_video_to_youtube(youtube, video_path, title, description, tags):
    """
    Uploads the generated video to YouTube.
    """
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # Category ID for People & Blogs; adjust as needed
        },
        "status": {
            "privacyStatus": "public"  # Options: 'public', 'private', 'unlisted'
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Upload progress: {int(status.progress() * 100)}%")
        logging.info("Video uploaded to YouTube successfully.")
        return response
    except Exception as e:
        logging.error(f"Error uploading video to YouTube: {e}")
        return None


# --------------------------------------------------------------------------------
# Generation Pipeline (shared by the async job runner and the no-JS fallback)
# --------------------------------------------------------------------------------

def missing_api_keys():
    """Return a list of required API keys that are not configured."""
    missing = []
    if not openai.api_key:
        missing.append("OPENAI_API_KEY")
    if not PEXELS_API_KEY:
        missing.append("PEXELS_API_KEY")
    return missing


def readiness():
    """Report which dependencies are configured/available for the UI status banner."""
    return {
        "openai": bool(openai.api_key),
        "pexels": bool(PEXELS_API_KEY),
        "imagemagick": bool(im_path and os.path.exists(im_path)),
    }


def list_history(limit=12):
    """List previously generated videos in the uploads folder, newest first."""
    items = []
    try:
        for name in os.listdir(UPLOADS_FOLDER):
            if not name.lower().endswith(".mp4"):
                continue
            path = os.path.join(UPLOADS_FOLDER, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            items.append({
                "name": name,
                "mtime": st.st_mtime,
                "size_mb": round(st.st_size / (1024 * 1024), 1),
            })
    except FileNotFoundError:
        return []
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


def run_pipeline(params, progress=lambda *a, **k: None):
    """
    Run the full topic -> video pipeline, reporting progress through `progress(stage, pct, message)`.
    Returns {"script", "video_path"(basename), "uploaded_link"} or raises on failure.
    """
    raw_topic = params["raw_topic"]
    topic = sanitize_filename(raw_topic)
    content_type = params.get("content_type", "video")
    ai_option = params.get("ai_option", "videos")
    voice_language = params.get("voice_language", "en")
    youtube_choice = params.get("youtube_choice", "no")
    authenticate_choice = params.get("authenticate_choice", "no")
    subtitles_on = params.get("subtitles_on", True)
    max_clips = params.get("max_clips", 3)
    aspect = params.get("aspect", "16:9")
    target_size = ASPECT_PRESETS.get(aspect)
    orientation = ASPECT_ORIENTATION.get(aspect, "landscape")
    available_langs = params["available_langs"]

    # Optional YouTube auth happens inside the job so the HTTP request never blocks on it.
    youtube = None
    if authenticate_choice == "yes":
        progress("auth", 5, "Authenticating with YouTube…")
        youtube = authenticate_youtube()

    length = 150 if content_type == "video" else 50
    language_name = available_langs.get(voice_language, "English")

    progress("script", 12, "Writing the script with AI…")
    prompt = f"Create a {length}-word YouTube script about {raw_topic} in {language_name}."
    script = generate_text_content(prompt, length)
    subtitles = script.split(". ")  # Subtitles: simple split by period & space

    progress("voiceover", 32, "Synthesizing the voiceover…")
    voiceover_file = os.path.join(OUTPUT_FOLDER, f"voiceover_{topic}.mp3")
    generate_voiceover(script, voiceover_file, language=voice_language)

    subs = subtitles if subtitles_on else []
    video_file = os.path.join(UPLOADS_FOLDER, f"{topic}.mp4")
    if ai_option == "images":
        progress("visuals", 52, "Generating AI images…")
        images = generate_ai_images(raw_topic, num_images=10)
        if not images:
            raise RuntimeError("Failed to generate images.")
        progress("assembly", 72, "Assembling the video…")
        video_path = create_video_from_images(images, voiceover_file, video_file, subs,
                                              target_size=target_size)
    elif ai_option == "videos":
        progress("visuals", 52, "Fetching stock footage from Pexels…")
        progress("assembly", 72, "Assembling the video…")
        video_path = create_video_from_pexels_clips_with_subtitles(
            raw_topic, voiceover_file, video_file, subs, max_clips=max_clips,
            target_size=target_size, orientation=orientation
        )
    else:
        raise RuntimeError("Invalid AI option selected.")

    if not video_path:
        raise RuntimeError("Failed to create the final video.")

    progress("export", 90, "Finalizing…")
    uploaded_link = None
    if youtube and youtube_choice == "yes":
        progress("export", 94, "Uploading to YouTube…")
        title = f"{raw_topic.capitalize()} - {content_type.capitalize()}"
        description = f"Explore this amazing {content_type} about {raw_topic}."
        tags = [content_type, "trending", raw_topic, "viral", "entertainment"]
        upload_response = upload_video_to_youtube(youtube, video_path, title, description, tags)
        if upload_response:
            video_id = upload_response.get("id")
            uploaded_link = f"https://www.youtube.com/watch?v={video_id}"

    progress("done", 100, "Your video is ready!")
    return {
        "script": script,
        "video_path": os.path.basename(video_path),
        "uploaded_link": uploaded_link,
    }


# In-memory job store for async generation (single-process Flask dev server).
_jobs = {}
_jobs_lock = threading.Lock()


def _set_job(job_id, **kw):
    with _jobs_lock:
        _jobs.setdefault(job_id, {}).update(kw)


def _get_job(job_id):
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _run_job(job_id, params):
    def progress(stage, pct, message):
        _set_job(job_id, stage=stage, progress=pct, message=message)
    try:
        result = run_pipeline(params, progress)
        _set_job(job_id, status="done", progress=100, stage="done",
                 message="Your video is ready!", result=result)
    except Exception as e:
        logging.error(f"Generation job {job_id} failed: {e}")
        _set_job(job_id, status="error",
                 message=str(e) or "Generation failed. Check the server logs.")


def _collect_params():
    """Pull and validate generation parameters from the current request form."""
    raw_topic = (request.form.get("topic") or "").strip()
    try:
        max_clips = max(1, min(8, int(request.form.get("clip_count", "3"))))
    except (TypeError, ValueError):
        max_clips = 3
    aspect = request.form.get("aspect", "16:9")
    if aspect not in ASPECT_PRESETS:
        aspect = "16:9"
    return {
        "raw_topic": raw_topic,
        "content_type": request.form.get("content_type", "video"),
        "ai_option": request.form.get("ai_option", "videos"),
        "voice_language": request.form.get("voice_language", "en"),
        "youtube_choice": request.form.get("youtube_upload", "no"),
        "authenticate_choice": request.form.get("authenticate", "no"),
        "subtitles_on": request.form.get("subtitles", "on") != "off",
        "max_clips": max_clips,
        "aspect": aspect,
        "available_langs": tts_langs(),
    }


# --------------------------------------------------------------------------------
# Flask Routes
# --------------------------------------------------------------------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """
    Serves uploaded/generated video files.
    """
    return send_from_directory(UPLOADS_FOLDER, filename)


@app.route("/generate", methods=["POST"])
def generate():
    """Start an async generation job and return its id (used by the live progress UI)."""
    missing = missing_api_keys()
    if missing:
        return jsonify({"error": f"API keys not configured: {', '.join(missing)}. "
                                 f"Create a .env file (see .env.example)."}), 400
    params = _collect_params()
    if not params["raw_topic"]:
        return jsonify({"error": "Please enter a topic."}), 400

    # Keep the in-memory store bounded by pruning the oldest finished jobs.
    with _jobs_lock:
        if len(_jobs) > 40:
            finished = [k for k, v in _jobs.items()
                        if v.get("status") in ("done", "error")]
            for k in finished[:len(_jobs) - 40]:
                _jobs.pop(k, None)

    job_id = uuid.uuid4().hex
    _set_job(job_id, status="running", stage="queued", progress=2,
             message="Starting the pipeline…", result=None)
    threading.Thread(target=_run_job, args=(job_id, params), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def job_status(job_id):
    """Return the current state of a generation job for the polling UI."""
    job = _get_job(job_id)
    if not job:
        return jsonify({"error": "Unknown or expired job."}), 404
    return jsonify(job)


@app.route("/health")
def health():
    """Lightweight readiness probe (API keys + ImageMagick)."""
    r = readiness()
    return jsonify({"status": "ok" if all(r.values()) else "degraded", "checks": r})


@app.route("/", methods=["GET", "POST"])
def index():
    # Get all available languages from gTTS
    available_langs = tts_langs()

    if request.method == "POST":
        # No-JS fallback: run synchronously and render the result page.
        missing = missing_api_keys()
        if missing:
            return render_template("index.html",
                                   error=f"API keys not configured: {', '.join(missing)}. "
                                         f"Create a .env file in the project root with your keys "
                                         f"(see .env.example for the template).",
                                   languages=available_langs)
        params = _collect_params()
        if not params["raw_topic"]:
            return render_template("index.html", error="Please enter a topic.",
                                   languages=available_langs)
        try:
            result = run_pipeline(params)
        except Exception as e:
            return render_template("index.html", error=str(e) or "Generation failed.",
                                   languages=available_langs)
        return render_template(
            "index.html",
            script=result["script"],
            video_path=result["video_path"],
            uploaded_link=result["uploaded_link"],
            languages=available_langs,
        )

    # If GET request, just render the form
    return render_template("index.html", languages=available_langs,
                           ready=readiness(), history=list_history())

if __name__ == "__main__":
    # Configurable via environment; debug defaults OFF (the Werkzeug debugger allows
    # arbitrary code execution if the port is ever exposed).
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)