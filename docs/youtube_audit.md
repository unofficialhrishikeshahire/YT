# YouTube API Project Audit & Privacy Policy Guide

## Why YouTube Uploads Default to "Private"
When you create a new developer project in the Google Cloud Console, Google automatically places the YouTube Data API v3 in **"Test / Unverified"** mode. Under Google's developer policy:
> Any video uploaded using an unverified third-party API project is automatically locked as **Private**.

This is why `config.yaml` defaults to:
```yaml
youtube:
  privacy_status: "private"
```

---

## Option 1: The Quick Manual Workflow (Zero Effort)
1. The pipeline uploads the weekly video as **Private**.
2. Agent 5 sends a Slack notification with the direct YouTube link.
3. You open [YouTube Studio](https://studio.youtube.com/) on your phone or laptop.
4. Click **Content**, click your video, and change visibility from **Private** to **Public** (or **Scheduled**).
5. Done! This takes approximately 15 seconds per week.

---

## Option 2: Requesting an Official Google API Audit (For 100% Automatic Public Uploads)
If you want the pipeline to directly publish videos as **Public** with no manual step:

### Steps to Submit for Audit:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **APIs & Services > OAuth consent screen**.
3. Fill out all application branding details:
   - App Name: e.g. `Weekly Documentary Publisher`
   - Privacy Policy Link: You can host a simple markdown privacy policy in your GitHub repository (`docs/privacy.md`).
   - Terms of Service Link: Same as above.
4. Under **Scopes**, ensure only `https://www.googleapis.com/auth/youtube.upload` is requested.
5. Click **Prepare for Verification** / **Submit for Verification**.
6. Google will send an automated questionnaire. State:
   - *"This is an internal personal automation tool to upload educational documentaries produced by my own automated content pipeline to my own YouTube channel."*
   - Provide a 1-minute screencast demonstrating the script uploading a video.
7. Once approved (typically 3–5 business days), update `config.yaml`:
   ```yaml
   youtube:
     privacy_status: "public"
   ```
