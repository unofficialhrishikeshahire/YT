"""Tests file handoff contracts and data schemas across all 5 agents."""

import json
from pathlib import Path
from src.utils.mock_data import MOCK_RESEARCH_MD, generate_mock_script


def test_research_md_contract(tmp_path: Path):
    research_file = tmp_path / "research.md"
    research_file.write_text(MOCK_RESEARCH_MD, encoding="utf-8")

    content = research_file.read_text(encoding="utf-8")
    assert "# Research Dossier:" in content
    assert "## Brief Documentation Summary" in content
    assert "## Key Facts & Timeline" in content
    assert "## Key Players" in content
    assert "## Current Situation & Analysis" in content
    assert "## What's Next" in content
    assert "## SOURCES" in content


def test_script_json_schema(tmp_path: Path):
    script_file = tmp_path / "script.json"
    scenes = generate_mock_script(word_count=1450)
    script_file.write_text(json.dumps(scenes), encoding="utf-8")

    loaded = json.loads(script_file.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    assert len(loaded) >= 5

    for scene in loaded:
        assert "scene_id" in scene
        assert "narration" in scene
        assert "estimated_duration_seconds" in scene
        assert scene["estimated_duration_seconds"] > 0


def test_visual_plan_schema(tmp_path: Path):
    plan_file = tmp_path / "visual_plan.json"
    mock_plan = {
        "style_guide": "Cinematic 35mm grain",
        "total_segments": 10,
        "hero_clips_count": 2,
        "segments": [
            {
                "segment_id": "seg_001",
                "scene_id": "scene_01",
                "visual_type": "hero_clip",
                "stock_keyword": "quantum computing",
                "image_prompt": "Cinematic server room",
                "video_prompt": "Camera tracking shot",
                "narration": "Deep inside subterranean facilities...",
            }
        ],
    }
    plan_file.write_text(json.dumps(mock_plan), encoding="utf-8")
    loaded = json.loads(plan_file.read_text(encoding="utf-8"))
    assert loaded["hero_clips_count"] <= 10
    assert len(loaded["segments"]) > 0
    assert loaded["segments"][0]["visual_type"] in ["stock", "ai_image", "hero_clip"]


def test_publisher_metadata_schema(tmp_path: Path):
    meta_file = tmp_path / "metadata.json"
    mock_meta = {
        "title": "Quantum Computing Breakthrough 2026",
        "description": "Full documentary deep dive with timestamps and sources.",
        "tags": ["quantum", "tech", "documentary"],
        "pinned_comment": "What do you think of this breakthrough?",
        "video_url": "https://www.youtube.com/watch?v=sample123",
    }
    meta_file.write_text(json.dumps(mock_meta), encoding="utf-8")
    loaded = json.loads(meta_file.read_text(encoding="utf-8"))
    assert len(loaded["title"]) <= 70
    assert "video_url" in loaded
    assert isinstance(loaded["tags"], list)
    assert len(loaded["pinned_comment"]) > 10
