from app.modules.attachments.enums import AttachmentEntityType

# ── File size limits ──────────────────────────────────────────────────────────
MAX_ATTACHMENT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB hard ceiling

# ── Allowed extensions & MIME types ──────────────────────────────────────────
# Lower-case extensions without leading dot.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        # Documents
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "csv", "odt",
        # Images
        "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "tiff",
        # Audio
        "mp3", "wav", "ogg", "m4a", "webm",
        # Video
        "mp4", "mov", "avi", "mkv",
        # Archives
        "zip", "tar", "gz", "7z",
        # Code / misc
        "json", "xml", "md", "yaml", "yml",
    }
)

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        # Documents
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/rtf",
        "text/csv",
        "application/vnd.oasis.opendocument.text",
        # Images
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "image/bmp",
        "image/tiff",
        # Audio
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/mp4",
        "audio/webm",
        # Video
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-matroska",
        "video/webm",
        # Archives
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-7z-compressed",
        # Code / misc
        "application/json",
        "application/xml",
        "text/xml",
        "text/markdown",
        "text/x-yaml",
        "application/x-yaml",
        # Generic binary fallback (browsers sometimes send this)
        "application/octet-stream",
    }
)

# Maximum filename length (original, before sanitisation)
MAX_FILENAME_LENGTH: int = 255
