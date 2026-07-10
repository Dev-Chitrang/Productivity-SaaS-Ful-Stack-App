import pytest

from app.modules.meetings.constants import (
    MAX_MEETING_TITLE_LENGTH,
    MAX_GUEST_NAME_LENGTH,
    MAX_GUEST_EMAIL_LENGTH,
    MEETING_URL_FORMAT,
    WSEvent,
)


class TestConstants:
    def test_max_meeting_title_length(self):
        assert MAX_MEETING_TITLE_LENGTH == 255
        assert isinstance(MAX_MEETING_TITLE_LENGTH, int)
        assert MAX_MEETING_TITLE_LENGTH > 0

    def test_max_guest_name_length(self):
        assert MAX_GUEST_NAME_LENGTH == 100
        assert isinstance(MAX_GUEST_NAME_LENGTH, int)
        assert MAX_GUEST_NAME_LENGTH > 0

    def test_max_guest_email_length(self):
        assert MAX_GUEST_EMAIL_LENGTH == 255
        assert isinstance(MAX_GUEST_EMAIL_LENGTH, int)
        assert MAX_GUEST_EMAIL_LENGTH > 0

    def test_meeting_url_format(self):
        assert MEETING_URL_FORMAT == "https://workspace.app/m/{code}"

    def test_meeting_url_format_substitution(self):
        code = "abc-defg-hij"
        expected = "https://workspace.app/m/abc-defg-hij"
        assert MEETING_URL_FORMAT.format(code=code) == expected


class TestWSEvent:
    def test_expected_event_strings_exist(self):
        assert WSEvent.PARTICIPANT_JOINED == "participant_joined"
        assert WSEvent.PARTICIPANT_WAITING == "participant_waiting"
        assert WSEvent.PARTICIPANT_LEFT == "participant_left"
        assert WSEvent.PARTICIPANT_ADMITTED == "participant_admitted"
        assert WSEvent.PARTICIPANT_REMOVED == "participant_removed"
        assert WSEvent.PARTICIPANT_REJECTED == "participant_rejected"
        assert WSEvent.MEETING_ENDED == "meeting_ended"
        assert WSEvent.STATUS_CHECK == "status_check"
        assert WSEvent.MUTE_CHANGED == "mute_changed"
        assert WSEvent.MUTED == "muted"
        assert WSEvent.SCREEN_SHARE_REQUESTED == "screen_share_requested"
        assert WSEvent.SCREEN_SHARE_PERMISSION_GRANTED == "screen_share_permission_granted"
        assert WSEvent.SCREEN_SHARE_PERMISSION_DENIED == "screen_share_permission_denied"
        assert WSEvent.SCREEN_SHARE_STARTED == "screen_share_started"
        assert WSEvent.SCREEN_SHARE_STOPPED == "screen_share_stopped"
        assert WSEvent.HOST_STOPPED_SCREEN_SHARE == "host_stopped_screen_share"
        assert WSEvent.HOST_LEFT == "host_left"
        assert WSEvent.ERROR == "error"

    def test_no_duplicate_values(self):
        values = [
            WSEvent.PARTICIPANT_JOINED,
            WSEvent.PARTICIPANT_WAITING,
            WSEvent.PARTICIPANT_LEFT,
            WSEvent.PARTICIPANT_ADMITTED,
            WSEvent.PARTICIPANT_REMOVED,
            WSEvent.PARTICIPANT_REJECTED,
            WSEvent.MEETING_ENDED,
            WSEvent.WAITING_ROOM_STATUS,
            WSEvent.STATUS_CHECK,
            WSEvent.MUTE_CHANGED,
            WSEvent.MUTED,
            WSEvent.SCREEN_SHARE_REQUESTED,
            WSEvent.SCREEN_SHARE_PERMISSION_GRANTED,
            WSEvent.SCREEN_SHARE_PERMISSION_DENIED,
            WSEvent.SCREEN_SHARE_STARTED,
            WSEvent.SCREEN_SHARE_STOPPED,
            WSEvent.HOST_STOPPED_SCREEN_SHARE,
            WSEvent.HOST_LEFT,
            WSEvent.ERROR,
        ]
        assert len(values) == len(set(values))
