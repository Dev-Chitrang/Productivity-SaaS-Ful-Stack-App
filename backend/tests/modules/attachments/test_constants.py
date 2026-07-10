import pytest
from app.modules.attachments.constants import (
    MAX_ATTACHMENT_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    ALLOWED_CONTENT_TYPES,
    MAX_FILENAME_LENGTH,
)


class TestAttachmentConstants:
    def test_max_attachment_size_bytes(self):
        assert MAX_ATTACHMENT_SIZE_BYTES == 50 * 1024 * 1024
        assert MAX_ATTACHMENT_SIZE_BYTES == 52428800

    def test_max_attachment_size_is_reasonable(self):
        assert MAX_ATTACHMENT_SIZE_BYTES >= 1
        assert MAX_ATTACHMENT_SIZE_BYTES <= 100 * 1024 * 1024

    def test_allowed_extensions_is_frozenset(self):
        assert isinstance(ALLOWED_EXTENSIONS, frozenset)

    def test_allowed_extensions_not_empty(self):
        assert len(ALLOWED_EXTENSIONS) > 0

    def test_allowed_extensions_contains_documents(self):
        assert "pdf" in ALLOWED_EXTENSIONS
        assert "docx" in ALLOWED_EXTENSIONS
        assert "txt" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_contains_images(self):
        assert "jpg" in ALLOWED_EXTENSIONS
        assert "jpeg" in ALLOWED_EXTENSIONS
        assert "png" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_contains_archives(self):
        assert "zip" in ALLOWED_EXTENSIONS
        assert "tar" in ALLOWED_EXTENSIONS
        assert "gz" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_lowercase(self):
        for ext in ALLOWED_EXTENSIONS:
            assert ext == ext.lower()
            assert "." not in ext

    def test_allowed_content_types_is_frozenset(self):
        assert isinstance(ALLOWED_CONTENT_TYPES, frozenset)

    def test_allowed_content_types_not_empty(self):
        assert len(ALLOWED_CONTENT_TYPES) > 0

    def test_allowed_content_types_contains_pdf(self):
        assert "application/pdf" in ALLOWED_CONTENT_TYPES

    def test_allowed_content_types_contains_text(self):
        assert "text/plain" in ALLOWED_CONTENT_TYPES

    def test_allowed_content_types_contains_image(self):
        assert "image/png" in ALLOWED_CONTENT_TYPES

    def test_allowed_content_types_contains_octet_stream(self):
        assert "application/octet-stream" in ALLOWED_CONTENT_TYPES

    def test_max_filename_length_positive(self):
        assert MAX_FILENAME_LENGTH > 0

    def test_max_filename_length_255(self):
        assert MAX_FILENAME_LENGTH == 255
