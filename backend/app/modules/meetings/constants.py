MAX_MEETING_TITLE_LENGTH = 255
MAX_GUEST_NAME_LENGTH = 100
MAX_GUEST_EMAIL_LENGTH = 255

# Base format matching workspace workspace.app/m/{meeting_code}
MEETING_URL_FORMAT = "https://workspace.app/m/{code}"

class WSEvent:
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_WAITING = "participant_waiting"
    PARTICIPANT_LEFT = "participant_left"
    PARTICIPANT_ADMITTED = "participant_admitted"
    PARTICIPANT_REMOVED = "participant_removed"
    PARTICIPANT_REJECTED = "participant_rejected"
    MEETING_ENDED = "meeting_ended"
    WAITING_ROOM_STATUS = "waiting_room_status"
    STATUS_CHECK = "status_check"
    MUTE_CHANGED = "mute_changed"
    MUTED = "muted"
    SCREEN_SHARE_REQUESTED = "screen_share_requested"
    SCREEN_SHARE_PERMISSION_GRANTED = "screen_share_permission_granted"
    SCREEN_SHARE_PERMISSION_DENIED = "screen_share_permission_denied"
    SCREEN_SHARE_STARTED = "screen_share_started"
    SCREEN_SHARE_STOPPED = "screen_share_stopped"
    HOST_STOPPED_SCREEN_SHARE = "host_stopped_screen_share"
    HOST_LEFT = "host_left"
    ERROR = "error"
