import pytest

from app.modules.meetings.transcript_preprocessor import preprocess_transcript


class TestPreprocessTranscript:
    def test_single_speaker_single_line(self):
        text = "Alice: Hello world"
        assert preprocess_transcript(text) == "Alice: Hello world"

    def test_multiple_speakers(self):
        text = """Alice: Hello everyone.

            Bob: Let's begin.

            Carol: I agree."""
        result = preprocess_transcript(text)
        assert "Alice:" in result
        assert "Bob:" in result
        assert "Carol:" in result
        assert "Hello everyone." in result
        assert "Let's begin." in result
        assert "I agree." in result
        assert "\n\n" not in result

    def test_strips_whitespace_only_lines(self):
        text = "Line 1\n\n\n\nLine 2"
        assert preprocess_transcript(text) == "Line 1 Line 2"

    def test_strips_leading_trailing_whitespace_per_line(self):
        text = "  Alice: Hi  \n\n  Bob: Hey  "
        result = preprocess_transcript(text)
        assert result == "Alice: Hi Bob: Hey"

    def test_empty_string(self):
        assert preprocess_transcript("") == ""

    def test_only_whitespace(self):
        assert preprocess_transcript("   \n\n   \n") == ""

    def test_preserves_speaker_names(self):
        text = """John:
            Hello everyone.

            Alice:
            Let's begin."""
        result = preprocess_transcript(text)
        assert result.startswith("John:")
        assert "Alice:" in result

    def test_no_extra_newlines_in_output(self):
        text = "A: 1\n\nB: 2\n\n\nC: 3"
        result = preprocess_transcript(text)
        assert "\n" not in result

    def test_large_transcript_compact(self):
        lines = [f"Speaker {i}: line {i}" for i in range(50)]
        text = "\n\n".join(lines)
        result = preprocess_transcript(text)
        assert result.count("Speaker") == 50
        assert "\n" not in result
