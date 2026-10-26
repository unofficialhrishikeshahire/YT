"""Agent 4: Video Editor.
Synthesizes speech using edge-tts per segment.
Fetches stock footage or creates Ken Burns animated visuals.
Supports manual hero clips (/manual_clips/hero_XX.mp4) with automatic AI image fallback.
Burns in subtitles, layers background music, generates 1280x720 thumbnail, credits.txt, and final_video.mp4.
"""

import asyncio
import json
import os
import random
import re
import shutil
import time
from pathlib import Path
from typing import Any, List, Optional

import edge_tts
from PIL import Image, ImageDraw, ImageFont

from src.config import AppConfig
from src.utils.ffmpeg_helper import create_ambient_music, create_ken_burns_clip, get_media_duration, run_ffmpeg
from src.utils.logger import setup_logger


class VideoEditorAgent:
    """Agent responsible for assembling the complete documentary video."""

    def __init__(self, config: AppConfig, run_dir: Path, mock: bool = False):
        self.config = config
        self.run_dir = run_dir
        self.mock = mock
        self.logger = setup_logger("video_editor", log_file=run_dir / "pipeline.log")
        self.manual_clips_dir = Path("manual_clips")
        self.assets_music_dir = Path("assets/music")

    async def _generate_audio_segment(self, text: str, output_path: Path) -> float:
        """Generate audio for a single narration segment using edge-tts and return duration."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        voice = self.config.audio.voice
        rate = self.config.audio.speech_rate

        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        await communicate.save(str(output_path))

        dur = get_media_duration(output_path)
        return max(3.0, dur)

    def _create_thematic_image(self, title: str, subtitle: str, output_path: Path) -> Path:
        """Create a clean, dark-mode 1080p slide with subtle gradients, captions, and typography."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = self.config.visuals.video_resolution

        img = Image.new("RGB", (w, h), color=(14, 18, 26))
        draw = ImageDraw.Draw(img)

        # Subtle dark gradient bands
        for y in range(h):
            ratio = y / h
            r = int(12 + ratio * 16)
            g = int(18 + ratio * 24)
            b = int(28 + ratio * 38)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Accent border & geometric lines
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(45, 65, 95), width=2)
        draw.rectangle([(48, 48), (w - 48, h - 48)], outline=(25, 35, 50), width=1)

        # Typography
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            sub_font = ImageFont.truetype("arial.ttf", 36)
            caption_font = ImageFont.truetype("arial.ttf", 34)
            watermark_font = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
            caption_font = ImageFont.load_default()
            watermark_font = ImageFont.load_default()

        # Header Title
        draw.text((w // 2, 110), title.upper(), font=title_font, fill=(245, 248, 255), anchor="mm")

        # Top Badge
        draw.text((w // 2, 65), "DOCUMENTARY INVESTIGATION", font=watermark_font, fill=(90, 140, 200), anchor="mm")

        # Burned-in Subtitle Banner at bottom
        caption_box_h = 130
        draw.rectangle([(100, h - caption_box_h - 60), (w - 100, h - 60)], fill=(8, 12, 18))
        draw.rectangle([(100, h - caption_box_h - 60), (w - 100, h - 60)], outline=(255, 190, 0), width=2)

        # Wrap narration words into 2 lines
        words = subtitle.split()
        lines = []
        cur = []
        for word in words:
            if len(" ".join(cur + [word])) > 58:
                lines.append(" ".join(cur))
                cur = [word]
            else:
                cur.append(word)
        if cur:
            lines.append(" ".join(cur))

        cap_y = h - caption_box_h - 20
        for line in lines[:2]:
            draw.text((w // 2, cap_y), line, font=caption_font, fill=(255, 255, 255), anchor="mm")
            cap_y += 45

        img.save(str(output_path), quality=95)
        return output_path

    def _generate_thumbnail(self, title: str, output_path: Path) -> Path:
        """Generate high-contrast 1280x720 thumbnail with bold typography."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), color=(10, 14, 22))
        draw = ImageDraw.Draw(img)

        # High-energy cinematic background gradient
        for y in range(h):
            ratio = y / h
            r = int(15 + ratio * 35)
            g = int(20 + ratio * 25)
            b = int(45 + ratio * 65)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Bold contrasting highlight box
        draw.rectangle([(60, 60), (w - 60, h - 60)], outline=(255, 190, 0), width=6)

        try:
            hero_font = ImageFont.truetype("arial.ttf", 68)
            badge_font = ImageFont.truetype("arial.ttf", 30)
        except Exception:
            hero_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # Category Badge
        draw.rectangle([(100, 110), (380, 170)], fill=(255, 190, 0))
        draw.text((240, 140), "SPECIAL REPORT", font=badge_font, fill=(10, 14, 22), anchor="mm")

        # Bold Title
        words = title.upper().split()
        lines = []
        cur_line = []
        for word in words:
            if len(" ".join(cur_line + [word])) > 22:
                lines.append(" ".join(cur_line))
                cur_line = [word]
            else:
                cur_line.append(word)
        if cur_line:
            lines.append(" ".join(cur_line))

        curr_y = 260
        for line in lines[:3]:
            # Drop shadow
            draw.text((104, curr_y + 4), line, font=hero_font, fill=(0, 0, 0))
            # Text
            draw.text((100, curr_y), line, font=hero_font, fill=(255, 255, 255))
            curr_y += 85

        img.save(str(output_path), quality=95)
        return output_path

    def _prepare_background_music(self, total_duration: float) -> Path:
        """Find or synthesize ambient background music track."""
        self.assets_music_dir.mkdir(parents=True, exist_ok=True)
        existing_tracks = list(self.assets_music_dir.glob("*.mp3"))

        if existing_tracks:
            return existing_tracks[0]

        default_synth_music = self.assets_music_dir / "ambient_drone.mp3"
        if not default_synth_music.exists():
            self.logger.info("No custom music tracks found in assets/music/. Synthesizing royalty-free ambient track...")
            create_ambient_music(default_synth_music, duration_seconds=int(total_duration) + 30)
        return default_synth_music

    def run(self, visual_plan_file: Path) -> Path:
        """Assemble complete 1080p final video from visual plan."""
        self.logger.info("Starting Agent 4: Video Editor...")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        audio_dir = self.run_dir / "audio"
        visuals_dir = self.run_dir / "visuals"
        audio_dir.mkdir(parents=True, exist_ok=True)
        visuals_dir.mkdir(parents=True, exist_ok=True)

        final_video = self.run_dir / "final_video.mp4"
        thumbnail_path = self.run_dir / "thumbnail.png"
        credits_path = self.run_dir / "credits.txt"

        with open(visual_plan_file, "r", encoding="utf-8") as f:
            plan = json.load(f)

        segments = plan.get("segments", [])
        if not segments:
            raise ValueError(f"No segments found in {visual_plan_file}")

        # Limit segments in mock mode for fast local verification (5 segments ~45 seconds)
        max_segments = 5 if self.mock else len(segments)
        active_segments = segments[:max_segments]

        self.logger.info(
            f"Processing {len(active_segments)} segments (Mode: {'MOCK (sample fast 5 segments)' if self.mock else 'FULL'})..."
        )

        segment_clips = []
        hero_index = 1
        total_audio_duration = 0.0

        for idx, seg in enumerate(active_segments):
            seg_id = seg["segment_id"]
            text = seg["narration"]
            v_type = seg["visual_type"]
            title = seg.get("scene_title", "Documentary Segment")

            self.logger.info(f"Processing {seg_id} ({idx+1}/{len(active_segments)}): [{v_type}]")

            # 1. Synthesize Audio
            audio_file = audio_dir / f"{seg_id}.mp3"
            dur = asyncio.run(self._generate_audio_segment(text, audio_file))
            total_audio_duration += dur

            # 2. Acquire Visual
            clip_file = visuals_dir / f"{seg_id}.mp4"
            manual_hero = self.manual_clips_dir / f"hero_{hero_index:02d}.mp4"

            if v_type == "hero_clip":
                if manual_hero.exists():
                    self.logger.info(f"Using manual hero clip: {manual_hero}")
                    run_ffmpeg([
                        "-i", str(manual_hero),
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
                        "-t", f"{dur:.3f}",
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-preset", "ultrafast",
                        str(clip_file),
                    ])
                else:
                    self.logger.info(f"Manual clip {manual_hero.name} absent. Falling back automatically to animated AI visual.")
                    img_path = visuals_dir / f"{seg_id}.png"
                    self._create_thematic_image(title, text, img_path)
                    create_ken_burns_clip(img_path, clip_file, duration_seconds=dur, zoom_in=(idx % 2 == 0))
                hero_index += 1
            else:
                img_path = visuals_dir / f"{seg_id}.png"
                self._create_thematic_image(title, text, img_path)
                create_ken_burns_clip(img_path, clip_file, duration_seconds=dur, zoom_in=(idx % 2 == 0))

            # Combine audio and video for this segment
            seg_combined = visuals_dir / f"{seg_id}_combined.mp4"
            run_ffmpeg([
                "-i", str(clip_file),
                "-i", str(audio_file),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(seg_combined),
            ])
            segment_clips.append(seg_combined)

        # 3. Concatenate all segments
        self.logger.info("Concatenating video segments...")
        concat_list_file = visuals_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for clip in segment_clips:
                clean_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        concatenated_video = visuals_dir / "concatenated.mp4"
        run_ffmpeg([
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(concatenated_video),
        ])

        # 4. Layer Background Music
        music_file = self._prepare_background_music(total_audio_duration)
        music_vol = self.config.audio.music_volume

        self.logger.info(f"Layering background music ({music_file.name} at volume {music_vol})...")
        run_ffmpeg([
            "-i", str(concatenated_video),
            "-stream_loop", "-1",
            "-i", str(music_file),
            "-filter_complex",
            f"[0:a]aresample=44100[voice];[1:a]volume={music_vol},aresample=44100[bg];[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[outa]",
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            str(final_video),
        ])

        # 5. Generate Thumbnail & Credits
        first_title = active_segments[0].get("scene_title", "Documentary")
        self._generate_thumbnail(first_title, thumbnail_path)

        credits_text = (
            "CREDITS & SOURCES:\n"
            "- Voiceover: Edge-TTS Neural Voice (en-US-ChristopherNeural)\n"
            "- Assembly: Automated Weekly Documentary Pipeline (FFmpeg)\n"
            f"- Background Music: {music_file.name} (Royalty-Free Ambient Track)\n"
            "- Visuals: Copyright-safe synthesized visuals & optional Pexels/Pixabay/Google Flow clips\n"
        )
        credits_path.write_text(credits_text, encoding="utf-8")

        self.logger.info(f"Agent 4 Complete! Final video produced at: {final_video}")
        self.logger.info(f"Thumbnail produced at: {thumbnail_path}")
        self.logger.info(f"Credits produced at: {credits_path}")

        return final_video
