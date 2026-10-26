"""Agent 1: Researcher.
Uses Gemini with Google Search grounding to discover and research trending, documentary-worthy topics.
Outputs /output/<run_id>/research.md and updates topics_history.json.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.utils.mock_data import MOCK_RESEARCH_MD
from src.utils.retry import retry_with_backoff


class ResearcherAgent:
    """Agent responsible for selecting and researching a trending documentary topic."""

    def __init__(self, config: AppConfig, run_dir: Path, mock: bool = False):
        self.config = config
        self.run_dir = run_dir
        self.mock = mock
        self.logger = setup_logger("researcher", log_file=run_dir / "pipeline.log")
        self.history_file = Path("topics_history.json")

    def _load_history(self) -> list[str]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [item.get("topic", "") for item in data if isinstance(item, dict)]
        except Exception as e:
            self.logger.warning(f"Could not load topics history: {e}")
            return []

    def _save_history(self, chosen_topic: str) -> None:
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.append({
                "topic": chosen_topic,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            self.logger.info(f"Recorded chosen topic to {self.history_file}")
        except Exception as e:
            self.logger.error(f"Failed to record topic in history: {e}")

    @retry_with_backoff(max_retries=5, base_delay=3.0)
    def _call_gemini_with_search(self, client: genai.Client, prompt: str) -> str:
        """Call Gemini API with Google Search grounding tool and rate limit retry."""
        time.sleep(self.config.api_limits.per_call_delay_seconds)
        
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        gen_config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=0.3,
        )
        
        response = client.models.generate_content(
            model=self.config.models.researcher_model,
            contents=prompt,
            config=gen_config,
        )
        
        if not response or not response.text:
            raise ValueError("Gemini returned empty response for research prompt")
            
        return response.text

    def run(self, topic_override: Optional[str] = None) -> Path:
        """Execute researcher agent and write research.md."""
        self.logger.info("Starting Agent 1: Researcher...")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.run_dir / "research.md"

        if self.mock:
            self.logger.info("[MOCK MODE] Using realistic pre-grounded research data.")
            output_file.write_text(MOCK_RESEARCH_MD.strip() + "\n", encoding="utf-8")
            self._save_history("The Quantum Advantage Race (2026 Breakthrough)")
            self.logger.info(f"Wrote research to {output_file}")
            return output_file

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Provide a free Google AI Studio key in .env or GitHub Secrets, or run with --mock."
            )

        client = genai.Client(api_key=api_key)
        past_topics = self._load_history()
        past_topics_str = ", ".join(f'"{t}"' for t in past_topics[-15:]) or "None"

        chosen_topic = topic_override
        if not chosen_topic:
            self.logger.info("Searching for this week's most relevant documentary topic with Google Search grounding...")
            selection_prompt = f"""You are an investigative documentary researcher.
Niche: {self.config.pipeline.default_niche}
Avoid repeating these past topics: [{past_topics_str}]

Find current trending topics in the news from this week using Google Search.
Select ONE topic that satisfies:
1. Documentary-worthy, educational, high public fascination.
2. Fact-checked, historical or technological significance.
3. Strict safety: NO unverified breaking crime/gossip, NO legal accusations against living individuals, NO graphic violence.

Output strictly in this format:
TOPIC: <Exact Title of Selected Topic>
REASON: <2 sentence justification of why it is trending and documentary-worthy>
"""
            selection_response = self._call_gemini_with_search(client, selection_prompt)
            self.logger.info(f"Topic Selection Result:\n{selection_response}")

            for line in selection_response.splitlines():
                if line.strip().startswith("TOPIC:"):
                    chosen_topic = line.replace("TOPIC:", "").strip()
                    break

            if not chosen_topic:
                chosen_topic = selection_response.splitlines()[0].strip()

        self.logger.info(f"Selected Topic: '{chosen_topic}'. Conducting deep factual research...")

        deep_research_prompt = f"""You are a senior investigative journalist writing a comprehensive documentary dossier.
Topic: {chosen_topic}

Use Google Search grounding to retrieve verified facts, statistics, and timeline events from reputable publications.
Compile the dossier in markdown with the following mandatory sections:
# Research Dossier: {chosen_topic}

## Brief Documentation Summary
(2-3 paragraphs giving an executive summary of the topic and why it matters)

## Key Facts & Timeline
(Bullet points with precise dates, numbers, milestones)

## Key Players
(Organizations, scientists, companies, or public figures involved)

## Current Situation & Analysis
(In-depth analysis of the current status and underlying mechanics/implications)

## What's Next
(Projected developments, challenges, and future milestones over the next 1-5 years)

## SOURCES
(List every major claim with at least 2 independent reputable sources/links. If any claim is disputed or uncertain, explicitly label it as '[Unverified]' and advise exclusion from the narration.)

Requirements:
- Factual and objective tone.
- Do NOT fabricate quotes, numbers, or dates.
"""

        research_content = self._call_gemini_with_search(client, deep_research_prompt)
        output_file.write_text(research_content.strip() + "\n", encoding="utf-8")
        self._save_history(chosen_topic)
        self.logger.info(f"Agent 1 Complete. Research dossier written to: {output_file}")
        return output_file
