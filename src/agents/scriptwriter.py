"""Agent 2: Scriptwriter.
Reads research.md and writes a complete documentary script of 1,400 - 2,200 words (~9-15 minutes).
Validates word count and regenerates if out of bounds.
Outputs /output/<run_id>/script.json with scenes and estimated timings.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.utils.mock_data import generate_mock_script
from src.utils.retry import retry_with_backoff


class ScriptwriterAgent:
    """Agent responsible for transforming research dossier into a structured documentary script."""

    def __init__(self, config: AppConfig, run_dir: Path, mock: bool = False):
        self.config = config
        self.run_dir = run_dir
        self.mock = mock
        self.logger = setup_logger("scriptwriter", log_file=run_dir / "pipeline.log")

    @staticmethod
    def count_words(text: str) -> int:
        """Count clean words in text, ignoring markdown syntax and punctuation."""
        clean_text = re.sub(r"[#*_`~>\-]", " ", text)
        words = [w for w in clean_text.split() if w.strip()]
        return len(words)

    @retry_with_backoff(max_retries=5, base_delay=3.0)
    def _call_gemini_script(self, client: genai.Client, prompt: str) -> str:
        """Call Gemini API for script generation with backoff retry."""
        time.sleep(self.config.api_limits.per_call_delay_seconds)
        gen_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )
        response = client.models.generate_content(
            model=self.config.models.scriptwriter_model,
            contents=prompt,
            config=gen_config,
        )
        if not response or not response.text:
            raise ValueError("Gemini returned empty response for script generation")
        return response.text

    def _parse_script_scenes(self, script_text: str) -> list[dict[str, Any]]:
        """Parse structured script output into scene list with duration calculations."""
        # Try JSON parsing if the model returned raw JSON
        clean_text = script_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, list) and all("narration" in item for item in parsed):
                wpm = self.config.script.target_wpm
                for i, item in enumerate(parsed):
                    if "scene_id" not in item:
                        item["scene_id"] = f"scene_{i+1:02d}"
                    words = len(item["narration"].split())
                    item["estimated_duration_seconds"] = max(5, int((words / wpm) * 60))
                return parsed
        except Exception:
            pass

        # Fallback parser: split by Scene headers (e.g., [SCENE 1: Hook])
        scenes = []
        raw_scenes = re.split(r"(?:\[SCENE|\#\# Scene|\#\# SCENE)", script_text)
        wpm = self.config.script.target_wpm

        scene_idx = 1
        for block in raw_scenes:
            block = block.strip()
            if not block or len(block) < 30:
                continue

            lines = block.splitlines()
            title = lines[0].replace("]", "").replace(":", "").strip()
            narration = " ".join(lines[1:]).strip()
            # Remove stage directions like [Narrator:], [Pause], (Sound effect)
            narration = re.sub(r"\[.*?\]", "", narration)
            narration = re.sub(r"\(.*?\)", "", narration).strip()

            words = len(narration.split())
            if words < 10:
                continue

            duration = max(5, int((words / wpm) * 60))
            scenes.append({
                "scene_id": f"scene_{scene_idx:02d}",
                "scene_title": title or f"Part {scene_idx}",
                "narration": narration,
                "estimated_duration_seconds": duration,
            })
            scene_idx += 1

        if not scenes:
            # Fallback if no scene markers detected: chunk into 7 narrative blocks
            paragraphs = [p.strip() for p in script_text.split("\n\n") if len(p.strip()) > 40]
            for i, p in enumerate(paragraphs):
                clean_p = re.sub(r"\[.*?\]", "", p).strip()
                words = len(clean_p.split())
                duration = max(5, int((words / wpm) * 60))
                scenes.append({
                    "scene_id": f"scene_{i+1:02d}",
                    "scene_title": f"Act {i+1}",
                    "narration": clean_p,
                    "estimated_duration_seconds": duration,
                })

        return scenes

    def run(self, research_file: Path) -> Path:
        """Read research.md and produce a validated script.json."""
        self.logger.info("Starting Agent 2: Scriptwriter...")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.run_dir / "script.json"

        if not research_file.exists():
            raise FileNotFoundError(f"Missing required input from Agent 1: {research_file}")

        research_text = research_file.read_text(encoding="utf-8")

        if self.mock:
            self.logger.info("[MOCK MODE] Generating mock script with validated word count.")
            scenes = generate_mock_script(word_count=1550)
            total_words = sum(self.count_words(s["narration"]) for s in scenes)
            self.logger.info(f"Mock script generated: {len(scenes)} scenes, {total_words} words.")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(scenes, f, indent=2)
            return output_file

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Provide in .env or run with --mock.")

        client = genai.Client(api_key=api_key)
        min_words = self.config.script.min_words
        max_words = self.config.script.max_words
        max_attempts = self.config.script.max_regeneration_attempts

        attempt = 1
        word_feedback = ""
        final_scenes: list[dict[str, Any]] = []

        while attempt <= max_attempts:
            self.logger.info(
                f"Generating script attempt {attempt}/{max_attempts} (Target: {min_words}-{max_words} words)..."
            )

            prompt = f"""You are a master YouTube documentary scriptwriter (in the style of Vox, Johnny Harris, and Kurzgesagt).
Read the factual research dossier below and write a captivating, deeply informative video documentary script.

### RESEARCH DOSSIER
{research_text}

### SCRIPT STRUCTURE REQUIREMENTS
1. **Hook (First 15 seconds)**: High-stakes question or arresting fact that commands attention immediately.
2. **Context & Foundation**: Why this matters now and historical backdrop.
3. **Timeline & Escalation**: Step-by-step chronology of events and decisions.
4. **Key Players & Motives**: The organizations, scientists, or stakeholders driving the story.
5. **Current Situation & Deep Analysis**: How the technology/event works, hidden complexities, tradeoffs.
6. **What Happens Next**: Future implications over 1-5 years.
7. **Closing & Call-To-Action**: Reflective thought-provoking conclusion, asking viewers for their opinion, followed by a reminder to like, comment, and subscribe for weekly documentaries.

### HARD CONSTRAINTS
- **WORD COUNT**: Must be strictly between {min_words} and {max_words} words.
- **FACT INTEGRITY**: Rely ONLY on facts from the research dossier. Do NOT invent quotes, dates, or events. Exclude anything marked '[Unverified]'.
- **FORMAT**: Return a clean JSON array of scene objects:
[
  {{
    "scene_id": "scene_01",
    "scene_title": "Title of Scene",
    "narration": "Full narration text spoken by voiceover..."
  }}
]

{word_feedback}
"""

            raw_response = self._call_gemini_script(client, prompt)
            scenes = self._parse_script_scenes(raw_response)

            total_words = sum(self.count_words(s.get("narration", "")) for s in scenes)
            self.logger.info(f"Attempt {attempt} produced {len(scenes)} scenes with {total_words} total words.")

            if min_words <= total_words <= max_words:
                self.logger.info(f"SUCCESS: Script word count ({total_words}) is within required bounds ({min_words}-{max_words})!")
                final_scenes = scenes
                break
            else:
                self.logger.warning(
                    f"Word count {total_words} is outside valid range ({min_words} - {max_words})."
                )
                if total_words < min_words:
                    word_feedback = f"CRITICAL CORRECTION: Your previous script was too short ({total_words} words). You MUST expand your analysis, provide richer technical explanations, and reach at least {min_words} words."
                else:
                    word_feedback = f"CRITICAL CORRECTION: Your previous script was too long ({total_words} words). You MUST condense descriptions, be more concise, and stay strictly below {max_words} words."
                attempt += 1

        if not final_scenes:
            if scenes:
                self.logger.warning(
                    f"Reached max attempts ({max_attempts}). Proceeding with closest script ({total_words} words)."
                )
                final_scenes = scenes
            else:
                raise RuntimeError("Failed to generate a valid documentary script from research.")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_scenes, f, indent=2)

        self.logger.info(f"Agent 2 Complete. Validated script saved to: {output_file}")
        return output_file
