# Complete Zero-Cost Pipeline Setup Guide

This guide walks you step-by-step through setting up your automated weekly documentary pipeline. Once this one-time 15-minute setup is complete, the pipeline runs 100% automatically in the cloud on GitHub Actions every Sunday.

---

## Step 1: Getting a Free Gemini API Key from Google AI Studio
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your standard Google Account.
3. Click **"Get API key"** in the top-left sidebar.
4. Click **"Create API key"** (select or create a default Google Cloud project).
5. Copy the generated key.
6. Open your local `.env` file and set:
   ```env
   GEMINI_API_KEY=your_copied_key_here
   ```

*Note: The free tier provides 15 requests per minute and up to 1,500 requests per day at $0.00 cost, which is far more than the ~5 calls per week our pipeline requires.*

---

## Step 2: Creating a YouTube OAuth Client & Generating Refresh Token
Because YouTube Data API v3 requires user authorization to upload videos to your channel, you need an OAuth Client ID and a Refresh Token that works headlessly in GitHub Actions.

### A. Create OAuth Client in Google Cloud Console
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project (the same one or create a new project called `YouTube-Automation`).
3. In the search bar at the top, search for **"YouTube Data API v3"** and click **Enable**.
4. Go to **APIs & Services > OAuth consent screen**:
   - User Type: Select **External**, then click **Create**.
   - App name: Enter `Documentary Pipeline`.
   - User support email & Developer contact email: Enter your email.
   - Click **Save and Continue** through Scopes.
   - Under **Test users**, click **+ ADD USERS** and add your own Google email address (the one that owns your YouTube channel).
   - Click **Save and Continue**.
5. Go to **APIs & Services > Credentials**:
   - Click **+ CREATE CREDENTIALS** > **OAuth client ID**.
   - Application type: Select **Desktop app**.
   - Name: `Pipeline Desktop Client`.
   - Click **Create**.
   - Copy your **Client ID** and **Client Secret**.

### B. Generate Your Headless Refresh Token (1 Click)
In your project terminal, run our built-in script:
```bash
.\.venv\Scripts\python.exe scripts/get_youtube_token.py
```
1. Paste your `Client ID` and `Client Secret` when prompted.
2. A browser tab will open automatically asking you to log into your Google Account.
3. Select your YouTube channel and click **Allow** (if you see a "Google hasn't verified this app" screen, click **Advanced** > **Go to Documentary Pipeline (unsafe)**).
4. The terminal will immediately print your `YOUTUBE_REFRESH_TOKEN`!
5. Add these three values into `.env`:
   ```env
   YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=your_client_secret
   YOUTUBE_REFRESH_TOKEN=your_refresh_token
   ```

---

## Step 3: Creating a Free Slack Incoming Webhook
1. Go to [Slack API: Your Apps](https://api.slack.com/apps).
2. Click **Create New App** > **From scratch**.
3. App Name: `YouTube Documentary Bot`, select your Slack workspace, and click **Create App**.
4. In the left menu, select **Incoming Webhooks**, and toggle the switch to **On**.
5. Click **Add New Webhook to Workspace** at the bottom.
6. Choose the channel you want notifications sent to (e.g., `#youtube-alerts`), and click **Allow**.
7. Copy the generated **Webhook URL** and add it to `.env`:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```

---

## Step 4: Adding All Secrets to GitHub
To let GitHub Actions run the pipeline weekly in the cloud while your laptop is closed:
1. Create a GitHub repository and push this project:
   ```bash
   git init
   git add .
   git commit -m "Initial automated pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
3. Under **Repository secrets**, click **New repository secret** and add each secret:
   - `GEMINI_API_KEY`
   - `SLACK_WEBHOOK_URL`
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
   - `PEXELS_API_KEY` *(Optional)*
   - `PIXABAY_API_KEY` *(Optional)*

---

## Step 5: Running Locally for First Test
You can test the entire pipeline locally at any time:

### Full Local Test with Mock Responses (Zero API Quota used):
```bash
python -m src.orchestrator --mock
```

### Full Local Test in Dry-Run Mode (Uses live Gemini, skips uploading & Slack):
```bash
python -m src.orchestrator --dry-run
```

---

## Step 6: The Optional 20-Minute Weekly Step (Google Flow / Veo Hero Clips)
The pipeline is designed to be **100% autonomous**: if you do nothing, it uses AI Ken Burns animated slides and copyright-safe stock footage automatically.

However, if you want ultra-cinematic AI video clips:
1. Look in the latest `output/<run_id>/flow_prompts.txt` file generated during the run.
2. You will find up to 10 numbered cinematic video prompts (e.g., `HERO CLIP #01`).
3. Paste each prompt into [Google Flow / Veo](https://labs.google/fx/tools/flow).
4. Download the generated 8-second clips.
5. Save them directly into the `/manual_clips/` folder as `hero_01.mp4`, `hero_02.mp4`, etc.
6. When the video editor runs, it automatically detects these clips and inserts them at the exact climax points! If any clip is missing, it automatically falls back with zero errors.
