export const ParticipantStatus = Object.freeze({
  WAITING: "WAITING",
  ADMITTED: "ADMITTED",
  LEFT: "LEFT",
  REMOVED: "REMOVED",
  REJECTED: "REJECTED",
})

export const MeetingStatus = Object.freeze({
  CREATED: "CREATED",
  ACTIVE: "ACTIVE",
  IDLE: "IDLE",
  ENDED: "ENDED",
  CANCELLED: "CANCELLED",
})

export const ParticipantType = Object.freeze({
  REGISTERED: "REGISTERED",
  GUEST: "GUEST",
})

export const MEETING_STATUS_LABELS = {
  CREATED: "Created",
  ACTIVE: "Active",
  IDLE: "Idle",
  ENDED: "Ended",
  CANCELLED: "Cancelled",
}

export const MEETING_STATUS_CLASSES = {
  CREATED: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
  ACTIVE: "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
  IDLE: "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800",
  ENDED: "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-950 dark:text-gray-300 dark:border-gray-800",
  CANCELLED: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
}

export const WSEvent = Object.freeze({
  PARTICIPANT_JOINED: "participant_joined",
  PARTICIPANT_WAITING: "participant_waiting",
  PARTICIPANT_LEFT: "participant_left",
  PARTICIPANT_ADMITTED: "participant_admitted",
  PARTICIPANT_REMOVED: "participant_removed",
  PARTICIPANT_REJECTED: "participant_rejected",
  MEETING_ENDED: "meeting_ended",
  WAITING_ROOM_STATUS: "waiting_room_status",
  STATUS_CHECK: "status_check",
  MUTE_CHANGED: "mute_changed",
  MUTED: "muted",
  SCREEN_SHARE_REQUESTED: "screen_share_requested",
  SCREEN_SHARE_PERMISSION_GRANTED: "screen_share_permission_granted",
  SCREEN_SHARE_PERMISSION_DENIED: "screen_share_permission_denied",
  SCREEN_SHARE_STARTED: "screen_share_started",
  SCREEN_SHARE_STOPPED: "screen_share_stopped",
  HOST_STOPPED_SCREEN_SHARE: "host_stopped_screen_share",
  ERROR: "error",
})

export const MEETING_STATUS_DOTS = {
  CREATED: "bg-blue-500",
  ACTIVE: "bg-green-500",
  IDLE: "bg-yellow-500",
  ENDED: "bg-gray-500",
  CANCELLED: "bg-red-500",
}

export const MeetingType = Object.freeze({
  INSTANT: "INSTANT",
  SCHEDULED: "SCHEDULED",
})

export const MEETING_TYPE_LABELS = {
  INSTANT: "Instant",
  SCHEDULED: "Scheduled",
}

export const MEETING_TYPE_CLASSES = {
  INSTANT: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800",
  SCHEDULED: "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950 dark:text-cyan-300 dark:border-cyan-800",
}

/**
 * @typedef {Object} Meeting
 * @property {string} id
 * @property {string} host_id
 * @property {string} title
 * @property {string} [description]
 * @property {string} meeting_code
 * @property {string} meeting_link
 * @property {boolean} enable_recording
 * @property {boolean} enable_transcript
 * @property {string} status
 * @property {string} created_at
 * @property {string} updated_at
 * @property {string} [ended_at]
 * @property {string} [meeting_type]
 * @property {string} [scheduled_date]
 * @property {string} [scheduled_time]
 * @property {number} [duration]
 * @property {string} [timezone]
 * @property {string} [agenda]
 * @property {boolean} [enable_ai_analysis]
 * @property {boolean} [can_join]
 * @property {number} [invited_participants_count]
 */

/**
 * @typedef {Object} Participant
 * @property {string} id
 * @property {string} meeting_id
 * @property {string} [user_id]
 * @property {string} [user_name]
 * @property {string} [guest_name]
 * @property {string} participant_type
 * @property {string} joined_at
 * @property {string} [left_at]
 */
