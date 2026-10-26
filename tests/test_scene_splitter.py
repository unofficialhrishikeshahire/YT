"""Tests for the visual director scene splitter and segment duration logic."""

from src.agents.visual_director import VisualDirectorAgent


def test_narration_splitter_basic():
    narration = (
        "Right now, deep inside subterranean research facilities, humanity is unlocking a computational realm. "
        "For decades, quantum supremacy was dismissed as a distant science fiction fantasy. "
        "But in 2026, an undeniable breakthrough has quietly altered the trajectory of human technology forever."
    )
    segments = VisualDirectorAgent.split_narration_into_segments(narration, target_words=20)
    assert len(segments) >= 2
    for seg in segments:
        words = len(seg.split())
        assert words > 0


def test_narration_splitter_long_sentence():
    long_sentence = (
        "When transistors shrink to the width of a few atoms, quantum tunneling causes electrical signals to bleed "
        "through physical barriers, and classical computation hits a fundamental thermal ceiling where every complex problem "
        "in chemistry, materials discovery, and complex logistics demands exponentially more silicon than our planet could power."
    )
    segments = VisualDirectorAgent.split_narration_into_segments(long_sentence, target_words=20)
    # Long sentence with clauses should be split into multiple chunks
    assert len(segments) >= 2
