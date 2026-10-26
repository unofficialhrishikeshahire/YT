"""Agent 5: Publisher and Notifier.
Discovers YouTube trending autocomplete keywords.
Generates SEO title (<70 chars), description, tags, and pinned comment using Gemini.
Uploads 1080p video + thumbnail to YouTube Data API v3 headlessly via OAuth refresh token.
Sends rich Slack Incoming Webhook notifications for pipeline completions and failures.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, List, Optional

import requests
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.utils.retry import retry_with_backoff


class PublisherAgent:
    """Agent responsible for SEO optimization, YouTube upload, and Slack notification."""

    def __init__(self, config: AppConfig, run_dir: Path, mock: bool = False, dry_run: bool = False):
        self.config = config
        self.run_dir = run_dir
        self.mock = mock
        self.dry_run = dry_run
        self.logger = setup_logger("publisher", log_file=run_dir / "pipeline.log")

    def _fetch_youtube_autocomplete_tags(self, query: str) -> List[str]:
        """Fetch real-time YouTube search autocomplete suggestions."""
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={requests.utils.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                # Response is jsonp: window.google.ac.h(["query",[["tag1",0],...]])
                text = resp.text
                start = text.find("(")
                end = text.rfind(")")
                if start != -1 and end != -1:
                    data = json.loads(text[start+1:end])
                    if len(data) > 1 and isinstance(data[1], list):
                        return [item[0] for item in data[1] if isinstance(item, list)][:10]
        except Exception as e:
            self.logger.warning(f"YouTube autocomplete suggestion failed: {e}")

        # Optional PyTrends fallback wrapped safely in try/except
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="en-US", tz=360)
            pytrends.build_payload([query[:30]], timeframe="now 7-d")
            related = pytrends.related_queries()
            if related and query[:30] in related and related[query[:30]]["top"] is not None:
                return related[query[:30]]["top"]["query"].tolist()[:10]
        except Exception:
            pass

        return [query, f"{query} documentary", f"{query} explained", "tech news", "deep dive"]

    @retry_with_backoff(max_retries=5, base_delay=3.0)
    def _generate_metadata_with_gemini(
        self,
        topic: str,
        research_text: str,
        script_scenes: List[dict],
        credits_text: str,
        trending_tags: List[str],
    ) -> dict:
        """Generate high-performing YouTube SEO title, description, and tags."""
        if self.mock:
            return {
                "title": f"{topic[:60]} Explained",
                "description": (
                    f"A comprehensive documentary investigation into {topic}.\n\n"
                    "TIMESTAMPS:\n00:00 - Introduction & The Hook\n01:30 - The Classical Wall\n"
                    "03:15 - The Breakthrough\n06:00 - What Happens Next\n\n"
                    f"{credits_text}"
                ),
                "tags": trending_tags[:12],
                "pinned_comment": (
                    f"What surprised you the most about the developments in {topic}? "
                    "Share your perspectives below, and don't forget to subscribe for our weekly investigations!"
                ),
            }

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")

        client = genai.Client(api_key=api_key)

        prompt = f"""You are a master YouTube SEO strategist for high-retention documentaries (like Vox, Veritasium, Johnny Harris).
Topic: {topic}
Trending Search Keywords: {', '.join(trending_tags)}

Generate optimized YouTube metadata based on the research dossier and documentary scenes.

Requirements:
1. TITLE: Catchy, curiosity-inducing, factual. STRICT HARD LIMIT: UNDER 70 CHARACTERS.
2. DESCRIPTION:
   - High-hook 2-paragraph summary containing search keywords naturally.
   - Timestamps breakdown for viewer navigation.
   - Sources list and credits attribution.
3. TAGS: 10-15 highly searchable, relevant tags (comma-separated).
4. PINNED_COMMENT: Engaging question designed to start a community debate in the comments.

Output format strictly as JSON:
{{
  "title": "<Title under 70 chars>",
  "description": "<Full description with timestamps and credits>",
  "tags": ["tag1", "tag2", "tag3", ...],
  "pinned_comment": "<Engaging prompt for viewers>"
}}
"""
        time.sleep(self.config.api_limits.per_call_delay_seconds)
        gen_config = types.GenerateContentConfig(temperature=0.7, max_output_tokens=2048)
        resp = client.models.generate_content(
            model=self.config.models.publisher_model,
            contents=prompt,
            config=gen_config,
        )
        
        clean = resp.text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(clean)
            # Enforce strict 70 char title limit
            if len(data.get("title", "")) > 70:
                data["title"] = data["title"][:67] + "..."
            return data
        except Exception as e:
            self.logger.warning(f"Could not parse Gemini JSON response ({e}). Using rule-based fallback.")
            return {
                "title": f"{topic[:65]}",
                "description": f"Documentary investigation on {topic}.\n\n{credits_text}",
                "tags": trending_tags[:12],
                "pinned_comment": f"What are your thoughts on {topic}? Let us know below!",
            }

    def _upload_to_youtube(
        self,
        video_path: Path,
        thumbnail_path: Path,
        metadata: dict,
    ) -> str:
        """Headlessly upload final video and thumbnail to YouTube using OAuth Refresh Token."""
        if self.mock or self.dry_run:
            self.logger.info("[MOCK/DRY-RUN] Simulating YouTube upload. Skipping actual API request.")
            fake_video_id = "sample_vid_20261026"
            return f"https://www.youtube.com/watch?v={fake_video_id}"

        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

        if not all([client_id, client_secret, refresh_token]):
            self.logger.warning(
                "YouTube OAuth credentials missing (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN). "
                "Skipping actual upload."
            )
            return "https://www.youtube.com/watch?v=unconfigured_credentials"

        # Build headless OAuth credentials
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "categoryId": self.config.youtube.category_id,
                "defaultLanguage": self.config.pipeline.channel_language,
            },
            "status": {
                "privacyStatus": self.config.youtube.privacy_status,
                "selfDeclaredMadeForKids": False,
                # Altered content / synthetic media declaration
                "containsSyntheticMedia": self.config.youtube.contains_synthetic_media,
            },
        }

        self.logger.info(f"Uploading {video_path.name} to YouTube (Privacy: {self.config.youtube.privacy_status})...")
        media = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4",
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )
        response = request.execute()
        video_id = response.get("id")

        if not video_id:
            raise RuntimeError("YouTube API did not return a valid video ID.")

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        self.logger.info(f"Video uploaded successfully! Video URL: {video_url}")

        # Upload thumbnail
        if thumbnail_path.exists():
            self.logger.info(f"Setting video thumbnail: {thumbnail_path.name}...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
                ).execute()
                self.logger.info("Custom thumbnail set successfully.")
            except Exception as e:
                self.logger.warning(f"Could not upload custom thumbnail: {e}")

        return video_url

    def send_slack_notification(
        self,
        title: str,
        video_url: str,
        topic: str,
        sources: List[str],
        is_private: bool,
    ) -> None:
        """Send rich Slack message on successful pipeline completion."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            self.logger.info("SLACK_WEBHOOK_URL not configured. Skipping Slack notification.")
            return

        if self.mock or self.dry_run:
            self.logger.info(f"[MOCK/DRY-RUN] Slack notification payload ready for: {title}")
            return

        private_reminder = (
            "\n:lock: *Note:* Upload is currently **PRIVATE** (per Google API policy). "
            "Please review in YouTube Studio and switch to **Public** when ready!"
            if is_private else ""
        )

        sources_formatted = "\n".join(f"• {s}" for s in sources[:5]) or "• Documented in research.md"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":clapper: Weekly Documentary Pipeline Published!",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Topic Chosen:*\n{topic}"},
                    {"type": "mrkdwn", "text": f"*Video Link:*\n<{video_url}|Watch Video>"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Title:* {title}\n{private_reminder}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Verified Sources:*\n{sources_formatted}",
                },
            },
        ]

        try:
            resp = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
            if resp.status_code == 200:
                self.logger.info("Slack success notification sent successfully.")
            else:
                self.logger.warning(f"Slack webhook returned code {resp.status_code}: {resp.text}")
        except Exception as e:
            self.logger.warning(f"Failed to send Slack notification: {e}")

    @staticmethod
    def send_slack_failure_alert(agent_name: str, error_message: str) -> None:
        """Send urgent Slack alert when an error stops the pipeline."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        payload = {
            "text": f":rotating_light: *Pipeline Execution Alert!*\n*Agent:* `{agent_name}`\n*Error:* ```{error_message}```"
        }
        try:
            requests.post(webhook_url, json=payload, timeout=8)
        except Exception:
            pass

    def run(
        self,
        video_path: Path,
        thumbnail_path: Path,
        research_file: Path,
        script_file: Path,
    ) -> dict:
        """Execute Agent 5: SEO generation, YouTube publishing, and Slack notification."""
        self.logger.info("Starting Agent 5: Publisher and Notifier...")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = self.run_dir / "metadata.json"

        research_text = research_file.read_text(encoding="utf-8") if research_file.exists() else ""
        credits_text = (self.run_dir / "credits.txt").read_text(encoding="utf-8") if (self.run_dir / "credits.txt").exists() else ""

        with open(script_file, "r", encoding="utf-8") as f:
            script_scenes = json.load(f)

        # Extract topic from first line of research.md
        topic = "Weekly Technology & Science Documentary"
        for line in research_text.splitlines():
            if line.startswith("# Research Dossier:"):
                topic = line.replace("# Research Dossier:", "").strip()
                break

        # 1. Real-time trending keywords
        self.logger.info(f"Discovering trending autocomplete keywords for topic: '{topic}'...")
        trending_tags = self._fetch_youtube_autocomplete_tags(topic)

        # 2. Generate SEO metadata
        self.logger.info("Generating SEO-optimized title, description, and tags with Gemini...")
        metadata = self._generate_metadata_with_gemini(
            topic=topic,
            research_text=research_text,
            script_scenes=script_scenes,
            credits_text=credits_text,
            trending_tags=trending_tags,
        )

        # Save metadata.json
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        self.logger.info(f"Metadata saved to: {metadata_file}")

        # 3. Headless YouTube Upload
        video_url = self._upload_to_youtube(video_path, thumbnail_path, metadata)
        metadata["video_url"] = video_url

        # 4. Extract verified sources for notification
        sources = []
        in_sources = False
        for line in research_text.splitlines():
            if "## SOURCES" in line:
                in_sources = True
                continue
            if in_sources and line.strip().startswith(("1.", "2.", "3.", "4.", "•", "-")):
                sources.append(line.strip())

        # 5. Slack Notification
        is_private = self.config.youtube.privacy_status.lower() == "private"
        self.send_slack_notification(
            title=metadata["title"],
            video_url=video_url,
            topic=topic,
            sources=sources,
            is_private=is_private,
        )

        self.logger.info("Agent 5 Complete! Publishing & notification workflow finished.")
        return metadata
