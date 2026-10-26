# Automated Weekly YouTube Documentary Pipeline

A production-ready, fully cloud-hosted, **100% FREE** weekly pipeline that autonomously researches, scripts, plans, animates, edits, voices, and uploads a full documentary video about the week's most relevant trending topic to YouTube via GitHub Actions.

---

## 🏛 Architecture (5 Autonomous Agents)

```
[Agent 1: Researcher]
        │  (Gemini + Google Search Grounding)
        ▼
   research.md
        │
[Agent 2: Scriptwriter]
        │  (1,400 - 2,200 words, strict fact adherence)
        ▼
   script.json
        │
[Agent 3: Visual Director]
        │  (8-10s segments, stock queries, AI prompts, max 10 hero clips)
        ▼
visual_plan.json  +  flow_prompts.txt
        │
[Agent 4: Video Editor]
        │  (Edge-TTS, Ken Burns FX, FFmpeg assembly, ambient music)
        ▼
final_video.mp4  +  thumbnail.png  +  credits.txt
        │
[Agent 5: Publisher & Notifier]
        │  (YouTube autocomplete SEO, headless OAuth v3 upload, Slack webhook)
        ▼
YouTube Video Published + Slack Team Notification
```

---

## 💎 Zero-Cost Free-Tier Guarantee

| Component | Free-Tier Tool | Free Allowance & Strategy |
| :--- | :--- | :--- |
| **Topic Research & Script** | Google AI Studio (Gemini 2.5/1.5 Flash) | 15 RPM / 1,500 RPD free tier with built-in exponential backoff & delay pacing. |
| **Voiceover** | Microsoft Edge-TTS | 100% free high-quality neural voices (`en-US-ChristopherNeural`). |
| **Cloud Execution** | GitHub Actions | 2,000 free runner mins/month (pipeline renders in ~3-4 mins = ~16 mins/month). |
| **Video & Audio Assembly** | FFmpeg / ImageIO-FFmpeg / Pillow | Standalone binary with Ken Burns zoom/pan and auto-synthesized ambient drone audio. |
| **Publishing** | YouTube Data API v3 | 10,000 units/day quota (1 upload costs 1,600 units = 16% of daily quota once per week). |
| **Notifications** | Slack Incoming Webhook | 100% free incoming webhook for weekly summaries and error alerts. |

---

## 🚀 Quickstart

### 1. Local Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (FFmpeg binary is bundled automatically via imageio-ffmpeg)
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Run Locally in Mock Mode (Zero Quota Used)
Test the entire 5-agent pipeline offline in ~45 seconds without using any API tokens:
```powershell
python -m src.orchestrator --mock
```

### 3. Run Specific Agents
```powershell
# Run only researcher
python -m src.orchestrator --agent researcher --mock

# Run only scriptwriter
python -m src.orchestrator --agent scriptwriter --mock

# Run only video editor
python -m src.orchestrator --agent video_editor --mock
```

### 4. Run Automated Test Suite
```powershell
pytest -v
```

---

## ⚙️ Configuration (`config.yaml`)

You can customize voice, video length, privacy, models, and audio volumes without changing any Python code:
```yaml
models:
  researcher_model: "gemini-2.5-flash"
  scriptwriter_model: "gemini-2.5-flash"

script:
  min_words: 1400
  max_words: 2200
  target_wpm: 145

audio:
  voice: "en-US-ChristopherNeural"
  music_volume: 0.12

youtube:
  privacy_status: "private"  # 'private', 'unlisted', or 'public'
  contains_synthetic_media: true
```

---

## 📖 Detailed Guides

- 📘 **[docs/SETUP.md](docs/SETUP.md)**: Beginner-friendly guide for Google AI Studio API key, YouTube OAuth credentials, Slack Webhook, and GitHub Secrets.
- 🔒 **[docs/youtube_audit.md](docs/youtube_audit.md)**: How to publish privately, switch visibility, and request a Google Cloud project audit for public uploads.

---

## 🎬 Optional 20-Minute Weekly Hero Clips
If you want ultra-cinematic AI video clips:
1. Every run exports up to 10 cinematic video prompts to `output/<run_id>/flow_prompts.txt`.
2. Paste them into **Google Flow / Veo**.
3. Save downloaded clips into `/manual_clips/` as `hero_01.mp4`, `hero_02.mp4`, etc.
4. *If you skip this step, the pipeline automatically uses Ken Burns animated visuals so it NEVER blocks waiting for you!*
