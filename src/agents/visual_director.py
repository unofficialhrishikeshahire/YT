"""Agent 3: Visual Director.
Breaks script into segments of ~8-10 seconds each.
Generates stock search keywords, AI image prompts, and max 10 hero_clip prompts.
Outputs visual_plan.json and flow_prompts.txt.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any, List

from src.config import AppConfig
from src.utils.logger import setup_logger


class VisualDirectorAgent:
    """Agent responsible for visual planning and cinematic segment breakdown."""

    def __init__(self, config: AppConfig, run_dir: Path, mock: bool = False):
        self.config = config
        self.run_dir = run_dir
        self.mock = mock
        self.logger = setup_logger("visual_director", log_file=run_dir / "pipeline.log")

    @staticmethod
    def split_narration_into_segments(narration: str, target_words: int = 22) -> List[str]:
        """Split narration text into natural clause-based segments of ~8-10 seconds (~20-25 words)."""
        sentences = re.split(r"(?<=[.!?])\s+", narration.strip())
        segments = []
        current_chunk: List[str] = []
        current_word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()
            
            if len(words) > 30:
                clauses = re.split(r"(?<=[,;:\u2014\-])\s+", sentence)
                for clause in clauses:
                    c_words = len(clause.split())
                    if current_word_count + c_words > target_words and current_chunk:
                        segments.append(" ".join(current_chunk))
                        current_chunk = [clause]
                        current_word_count = c_words
                    else:
                        current_chunk.append(clause)
                        current_word_count += c_words
            else:
                if current_word_count + len(words) > target_words and current_chunk:
                    segments.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_word_count = len(words)
                else:
                    current_chunk.append(sentence)
                    current_word_count += len(words)

        if current_chunk:
            segments.append(" ".join(current_chunk))

        return segments

    def _generate_rule_based_plan(self, script_data: List[dict]) -> dict:
        """Create structured visual plan using domain-specific heuristics and styles."""
        segments = []
        seg_idx = 1
        hero_count = 0
        max_hero = self.config.visuals.max_hero_clips
        total_scenes = len(script_data)

        style_guide = (
            "Cinematic documentary style: 35mm film grain, moody anamorphic lighting, deep chiaroscuro, "
            "subtle volumetric mist, realistic textures, 8k resolution, color-graded in cold teals and warm ambers."
        )

        for s_idx, scene in enumerate(script_data):
            scene_id = scene.get("scene_id", f"scene_{s_idx+1:02d}")
            scene_title = scene.get("scene_title", "Documentary Segment")
            narration = scene.get("narration", "")

            raw_segments = self.split_narration_into_segments(narration, target_words=22)

            for part_idx, seg_text in enumerate(raw_segments):
                words = len(seg_text.split())
                est_sec = max(5, int((words / self.config.script.target_wpm) * 60))

                is_hero_candidate = (
                    (part_idx == 0 or s_idx == total_scenes - 2)
                    and hero_count < max_hero
                    and seg_idx % 4 == 1
                )

                if is_hero_candidate:
                    v_type = "hero_clip"
                    hero_count += 1
                elif seg_idx % 2 == 0:
                    v_type = "stock"
                else:
                    v_type = "ai_image"

                clean_words = re.findall(r"[A-Za-z]{4,}", seg_text)
                keyword = clean_words[0].lower() if clean_words else "technology"
                if len(clean_words) > 1:
                    keyword = f"{clean_words[0].lower()} {clean_words[1].lower()}"

                image_prompt = (
                    f"A cinematic high-detail shot illustrating: {seg_text[:120]}. "
                    f"{style_guide}"
                )
                video_prompt = (
                    f"Cinematic slow motion camera movement capturing {seg_text[:120]}. "
                    f"Photorealistic 8k, dramatic lighting, atmospheric depth, 24fps."
                )

                segments.append({
                    "segment_id": f"seg_{seg_idx:03d}",
                    "scene_id": scene_id,
                    "scene_title": scene_title,
                    "narration": seg_text,
                    "duration_seconds": est_sec,
                    "visual_type": v_type,
                    "stock_keyword": keyword,
                    "image_prompt": image_prompt,
                    "video_prompt": video_prompt,
                })
                seg_idx += 1

        return {
            "style_guide": style_guide,
            "total_segments": len(segments),
            "hero_clips_count": hero_count,
            "segments": segments,
        }

    def run(self, script_file: Path) -> Path:
        """Execute Agent 3: Visual Director and produce visual_plan.json and flow_prompts.txt."""
        self.logger.info("Starting Agent 3: Visual Director...")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        visual_plan_file = self.run_dir / "visual_plan.json"
        flow_prompts_file = self.run_dir / "flow_prompts.txt"

        if not script_file.exists():
            raise FileNotFoundError(f"Missing required script file: {script_file}")

        with open(script_file, "r", encoding="utf-8") as f:
            script_data = json.load(f)

        plan = self._generate_rule_based_plan(script_data)

        with open(visual_plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)

        hero_lines = [
            f"# Google Flow / Veo Prompts for Manual Generation (Max {self.config.visuals.max_hero_clips} clips)",
            f"# Drop downloaded clips into /manual_clips/ as hero_01.mp4, hero_02.mp4, etc.\n",
        ]
        h_idx = 1
        for seg in plan["segments"]:
            if seg["visual_type"] == "hero_clip":
                hero_lines.append(f"--- HERO CLIP #{h_idx:02d} (Segment: {seg['segment_id']}) ---")
                hero_lines.append(f"Prompt: {seg['video_prompt']}")
                hero_lines.append(f"Filename Target: manual_clips/hero_{h_idx:02d}.mp4")
                hero_lines.append(f"Narration context: \"{seg['narration']}\"\n")
                h_idx += 1

        flow_prompts_file.write_text("\n".join(hero_lines), encoding="utf-8")

        self.logger.info(
            f"Agent 3 Complete. Visual plan saved: {visual_plan_file} ({plan['total_segments']} segments, "
            f"{plan['hero_clips_count']} hero clips). Flow prompts written to: {flow_prompts_file}"
        )
        return visual_plan_file
