"""Unit tests for the script word counter and bounds validator."""

from src.agents.scriptwriter import ScriptwriterAgent


def test_word_counter_clean():
    text = "This is a clean sentence with eight words."
    assert ScriptwriterAgent.count_words(text) == 8


def test_word_counter_markdown_removal():
    text = "# Scene 1: The Hook\n**Hello** world! This is a *test* of `markdown` removal."
    # clean words: Scene, 1, The, Hook, Hello, world, This, is, a, test, of, markdown, removal (13 words)
    assert ScriptwriterAgent.count_words(text) == 13


def test_word_counter_boundaries():
    min_words = 1400
    max_words = 2200
    test_text = "word " * 1500
    words = ScriptwriterAgent.count_words(test_text)
    assert min_words <= words <= max_words
