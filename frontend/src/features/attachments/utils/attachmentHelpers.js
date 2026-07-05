/**
 * Pure helper utilities for the Attachment UI layer.
 * No API calls, no React hooks — safe to import anywhere.
 */

// ─── File size formatting ─────────────────────────────────────────────────────

export function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return "0 B"
    const units = ["B", "KB", "MB", "GB"]
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
    return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

// ─── Date formatting ──────────────────────────────────────────────────────────

export function formatUploadDate(iso) {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    })
}

// ─── Extension / MIME classification ────────────────────────────────────────

const IMAGE_EXTS = new Set(["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "svg"])
const PDF_EXTS = new Set(["pdf"])
const TEXT_EXTS = new Set(["txt", "md", "csv", "json", "xml", "yaml", "yml", "rtf"])
const AUDIO_EXTS = new Set(["mp3", "wav", "ogg", "m4a", "webm"])
const VIDEO_EXTS = new Set(["mp4", "mov", "avi", "mkv"])
const DOC_EXTS = new Set(["doc", "docx", "odt"])
const XLS_EXTS = new Set(["xls", "xlsx"])
const PPT_EXTS = new Set(["ppt", "pptx"])
const ZIP_EXTS = new Set(["zip", "tar", "gz", "7z"])
const CODE_EXTS = new Set(["js", "ts", "jsx", "tsx", "py", "java", "c", "cpp", "html", "css"])

export const FileCategory = {
    IMAGE: "IMAGE",
    PDF: "PDF",
    TEXT: "TEXT",
    AUDIO: "AUDIO",
    VIDEO: "VIDEO",
    DOCUMENT: "DOCUMENT",
    SHEET: "SHEET",
    SLIDE: "SLIDE",
    ARCHIVE: "ARCHIVE",
    CODE: "CODE",
    OTHER: "OTHER",
}

export function getFileCategory(extension) {
    const ext = (extension || "").toLowerCase()
    if (IMAGE_EXTS.has(ext)) return FileCategory.IMAGE
    if (PDF_EXTS.has(ext)) return FileCategory.PDF
    if (TEXT_EXTS.has(ext)) return FileCategory.TEXT
    if (AUDIO_EXTS.has(ext)) return FileCategory.AUDIO
    if (VIDEO_EXTS.has(ext)) return FileCategory.VIDEO
    if (DOC_EXTS.has(ext)) return FileCategory.DOCUMENT
    if (XLS_EXTS.has(ext)) return FileCategory.SHEET
    if (PPT_EXTS.has(ext)) return FileCategory.SLIDE
    if (ZIP_EXTS.has(ext)) return FileCategory.ARCHIVE
    if (CODE_EXTS.has(ext)) return FileCategory.CODE
    return FileCategory.OTHER
}

/**
 * Returns true if the file can be previewed inline in the browser
 * (images open as blob URLs, PDFs/text open in a new tab via blob URL).
 */
export function canPreviewInBrowser(extension, contentType) {
    const cat = getFileCategory(extension)
    if (cat === FileCategory.IMAGE) return true
    if (cat === FileCategory.PDF) return true
    if (cat === FileCategory.TEXT) return true
    return false
}

/**
 * Returns true if the attachment is an image that can be shown as <img>.
 */
export function isImageFile(extension) {
    return getFileCategory(extension) === FileCategory.IMAGE
}

// ─── Programmatic file download ──────────────────────────────────────────────

/**
 * Triggers a browser download from a Blob (axios responseType:"blob" response).
 * Never exposes a storage path — uses an ephemeral Object URL.
 */
export function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

/**
 * Opens a Blob in a new browser tab (PDF, images, text).
 */
export function openBlobInNewTab(blob, contentType) {
    const b = contentType ? new Blob([blob], { type: contentType }) : blob
    const url = URL.createObjectURL(b)
    window.open(url, "_blank", "noopener,noreferrer")
    // Cannot revoke immediately because the new tab needs time to load.
    // The browser will clean it up on tab close.
}
