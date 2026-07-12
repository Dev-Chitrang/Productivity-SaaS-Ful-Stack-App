import pytest

from app.modules.ai_suggestions.enums import SuggestionStatus


class TestSuggestionStatus:
    def test_values(self):
        assert SuggestionStatus.PENDING.value == "PENDING"
        assert SuggestionStatus.CREATED.value == "CREATED"
        assert SuggestionStatus.REJECTED.value == "REJECTED"

    def test_is_str_enum(self):
        # str(enum) yields the value because it subclasses str
        assert SuggestionStatus.PENDING == "PENDING"
        assert SuggestionStatus.CREATED == "CREATED"
        assert SuggestionStatus.REJECTED == "REJECTED"

    def test_membership(self):
        assert "PENDING" in [s.value for s in SuggestionStatus]
        assert "CREATED" in [s.value for s in SuggestionStatus]
        assert "REJECTED" in [s.value for s in SuggestionStatus]

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            SuggestionStatus("NOT_A_STATUS")

    def test_distinct_values(self):
        values = [s.value for s in SuggestionStatus]
        assert len(values) == len(set(values))
