import pytest

from app.modules.meetings.enums import (
    MeetingType,
    MeetingStatus,
    ParticipantType,
    ParticipantStatus,
    SessionStatus,
    AIAnalysisStatus,
)


class TestMeetingType:
    def test_values(self):
        assert MeetingType.INSTANT == "INSTANT"
        assert MeetingType.SCHEDULED == "SCHEDULED"

    def test_is_str_enum(self):
        assert issubclass(MeetingType, str)

    def test_members(self):
        assert set(MeetingType) == {"INSTANT", "SCHEDULED"}


class TestMeetingStatus:
    def test_values(self):
        assert MeetingStatus.CREATED == "CREATED"
        assert MeetingStatus.SCHEDULED == "SCHEDULED"
        assert MeetingStatus.ACTIVE == "ACTIVE"
        assert MeetingStatus.IDLE == "IDLE"
        assert MeetingStatus.ENDED == "ENDED"
        assert MeetingStatus.CANCELLED == "CANCELLED"

    def test_is_str_enum(self):
        assert issubclass(MeetingStatus, str)

    def test_members(self):
        assert set(MeetingStatus) == {
            "CREATED",
            "SCHEDULED",
            "ACTIVE",
            "IDLE",
            "ENDED",
            "CANCELLED",
        }


class TestParticipantType:
    def test_values(self):
        assert ParticipantType.REGISTERED == "REGISTERED"
        assert ParticipantType.GUEST == "GUEST"

    def test_is_str_enum(self):
        assert issubclass(ParticipantType, str)

    def test_members(self):
        assert set(ParticipantType) == {"REGISTERED", "GUEST"}


class TestParticipantStatus:
    def test_values(self):
        assert ParticipantStatus.WAITING == "WAITING"
        assert ParticipantStatus.ADMITTED == "ADMITTED"
        assert ParticipantStatus.LEFT == "LEFT"
        assert ParticipantStatus.REMOVED == "REMOVED"
        assert ParticipantStatus.REJECTED == "REJECTED"
        assert ParticipantStatus.DISCONNECTED == "DISCONNECTED"

    def test_is_str_enum(self):
        assert issubclass(ParticipantStatus, str)

    def test_members(self):
        assert set(ParticipantStatus) == {
            "WAITING",
            "ADMITTED",
            "LEFT",
            "REMOVED",
            "REJECTED",
            "DISCONNECTED",
        }


class TestSessionStatus:
    def test_values(self):
        assert SessionStatus.ACTIVE == "ACTIVE"
        assert SessionStatus.ENDED == "ENDED"
        assert SessionStatus.CANCELLED == "CANCELLED"

    def test_is_str_enum(self):
        assert issubclass(SessionStatus, str)

    def test_members(self):
        assert set(SessionStatus) == {"ACTIVE", "ENDED", "CANCELLED"}


class TestAIAnalysisStatus:
    def test_values(self):
        assert AIAnalysisStatus.PENDING == "PENDING"
        assert AIAnalysisStatus.PROCESSING == "PROCESSING"
        assert AIAnalysisStatus.COMPLETED == "COMPLETED"
        assert AIAnalysisStatus.FAILED == "FAILED"

    def test_is_str_enum(self):
        assert issubclass(AIAnalysisStatus, str)

    def test_members(self):
        assert set(AIAnalysisStatus) == {
            "PENDING",
            "PROCESSING",
            "COMPLETED",
            "FAILED",
        }
