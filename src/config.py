"""Configuration loader with Pydantic validation."""

from pathlib import Path
from typing import List, Tuple
import yaml
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    name: str = "Weekly DeepDive Documentary"
    channel_language: str = "en"
    default_niche: str = "trending technology, science, and world events"


class ModelsConfig(BaseModel):
    researcher_model: str = "gemini-2.5-flash"
    scriptwriter_model: str = "gemini-2.5-flash"
    visual_director_model: str = "gemini-2.5-flash"
    publisher_model: str = "gemini-2.5-flash"


class ApiLimitsConfig(BaseModel):
    max_retries: int = Field(default=5, ge=1, le=10)
    base_backoff_seconds: float = Field(default=3.0, ge=1.0)
    max_backoff_seconds: float = Field(default=60.0, ge=10.0)
    per_call_delay_seconds: float = Field(default=2.0, ge=0.5)


class ScriptConfig(BaseModel):
    min_words: int = Field(default=1400, ge=500)
    max_words: int = Field(default=2200, le=4000)
    target_wpm: int = Field(default=145, ge=100, le=200)
    max_regeneration_attempts: int = Field(default=3, ge=1, le=5)


class VisualsConfig(BaseModel):
    segment_duration_target_seconds: int = Field(default=9, ge=5, le=15)
    max_hero_clips: int = Field(default=10, ge=1, le=20)
    video_resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30


class AudioConfig(BaseModel):
    voice: str = "en-US-ChristopherNeural"
    music_volume: float = Field(default=0.12, ge=0.0, le=1.0)
    speech_rate: str = "+0%"


class YouTubeConfig(BaseModel):
    privacy_status: str = "private"
    contains_synthetic_media: bool = True
    category_id: str = "28"


class SlackConfig(BaseModel):
    notify_on_success: bool = True
    notify_on_failure: bool = True


class AppConfig(BaseModel):
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    api_limits: ApiLimitsConfig = Field(default_factory=ApiLimitsConfig)
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    visuals: VisualsConfig = Field(default_factory=VisualsConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    youtube: YouTubeConfig = Field(default_factory=YouTubeConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)


def load_config(config_path: Path | str = "config.yaml") -> AppConfig:
    """Load and validate configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return AppConfig(**data)
