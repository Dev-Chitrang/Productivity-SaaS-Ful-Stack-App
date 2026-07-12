import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.core.storage import validate_uploaded_file, EXTENSION_TO_MIMES
from app.modules.attachments.constants import MAX_ATTACHMENT_SIZE_BYTES
from app.modules.attachments.exceptions import AttachmentValidationError


class TestValidateUploadedFile:
    def test_empty_content_raises(self):
        with pytest.raises(AttachmentValidationError, match="Invalid file type."):
            validate_uploaded_file("file.pdf", b"")

    def test_content_too_large_raises(self):
        large_content = b"x" * (MAX_ATTACHMENT_SIZE_BYTES + 1)
        with pytest.raises(AttachmentValidationError, match="too large"):
            validate_uploaded_file("file.pdf", large_content)

    def test_max_size_accepted(self):
        content = b"x" * MAX_ATTACHMENT_SIZE_BYTES
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            # We also need the extension to be allowed
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"pdf"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"pdf": {"application/pdf"}}):
                    mime = validate_uploaded_file("file.pdf", content)
                    assert mime == "application/pdf"

    def test_invalid_extension_raises(self):
        with pytest.raises(AttachmentValidationError, match="Unsupported extension"):
            validate_uploaded_file("file.unknown", b"content")

    def test_valid_pdf_accepted(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"pdf"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"pdf": {"application/pdf"}}):
                    mime = validate_uploaded_file("file.pdf", b"%PDF-1.4")
                    assert mime == "application/pdf"

    def test_magic_detection_failure_raises(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.side_effect = Exception("libmagic error")
            with pytest.raises(AttachmentValidationError, match="Invalid file type."):
                validate_uploaded_file("file.pdf", b"content")

    def test_empty_mime_raises(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = ""
            with pytest.raises(AttachmentValidationError, match="Invalid file type."):
                validate_uploaded_file("file.pdf", b"content")

    def test_mime_mismatch_raises(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "image/jpeg"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"pdf"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"pdf": {"application/pdf"}}):
                    with pytest.raises(AttachmentValidationError, match="do not match extension"):
                        validate_uploaded_file("file.pdf", b"content")

    def test_extension_missing_mimes_map_raises(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "application/pdf"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"xyz"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {}):
                    with pytest.raises(AttachmentValidationError, match="do not match extension"):
                        validate_uploaded_file("file.xyz", b"content")

    def test_detected_mime_is_lowercased(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "Application/PDF"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"pdf"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"pdf": {"application/pdf"}}):
                    mime = validate_uploaded_file("file.pdf", b"content")
                    assert mime == "application/pdf"

    def test_case_insensitive_extension(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "text/plain"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"txt"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"txt": {"text/plain"}}):
                    mime = validate_uploaded_file("file.TXT", b"hello")
                    assert mime == "text/plain"

    def test_extension_with_leading_dot_accepted(self):
        with patch("app.core.storage.magic") as mock_magic:
            mock_magic.from_buffer.return_value = "text/plain"
            with patch("app.core.storage.ALLOWED_EXTENSIONS", {"txt"}):
                with patch("app.core.storage.EXTENSION_TO_MIMES", {"txt": {"text/plain"}}):
                    mime = validate_uploaded_file("file.txt", b"hello")
                    assert mime == "text/plain"


class TestExtensionToMimes:
    def test_contains_pdf(self):
        assert "pdf" in EXTENSION_TO_MIMES
        assert "application/pdf" in EXTENSION_TO_MIMES["pdf"]

    def test_contains_docx(self):
        assert "docx" in EXTENSION_TO_MIMES
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in EXTENSION_TO_MIMES["docx"]

    def test_contains_txt(self):
        assert "txt" in EXTENSION_TO_MIMES
        assert "text/plain" in EXTENSION_TO_MIMES["txt"]

    def test_all_entries_are_sets(self):
        for ext, mimes in EXTENSION_TO_MIMES.items():
            assert isinstance(mimes, set)
            assert len(mimes) > 0


class TestLocalStorageProvider:
    @pytest.fixture
    def tmp_base(self, tmp_path):
        return str(tmp_path / "storage")

    @pytest.fixture
    def provider(self, tmp_base):
        from app.core.storage import LocalStorageProvider
        return LocalStorageProvider(tmp_base)

    async def test_save_creates_file(self, provider, tmp_base):
        import uuid
        session_id = uuid.uuid4()
        result = await provider.save(session_id, "recordings", "test.webm", b"content", "audio/webm")
        assert result["filename"] == "test.webm"
        assert result["size"] == 7
        assert "storage_path" in result

    async def test_save_to_path_creates_file(self, provider, tmp_base):
        result = await provider.save_to_path("custom_dir", "test.txt", b"hello", "text/plain")
        assert result["filename"] == "test.txt"
        assert result["size"] == 5
        assert result["stored_filename"].endswith("_test.txt")

    async def test_delete_existing_file(self, provider, tmp_base):
        import uuid
        session_id = uuid.uuid4()
        result = await provider.save(session_id, "test", "file.txt", b"data", "text/plain")
        assert provider.exists(result["storage_path"]) is True
        deleted = await provider.delete(result["storage_path"])
        assert deleted is True
        assert provider.exists(result["storage_path"]) is False

    async def test_delete_non_existent_file(self, provider):
        deleted = await provider.delete("/nonexistent/file.txt")
        assert deleted is False

    def test_get_absolute_path(self, provider):
        assert provider.get_absolute_path("/some/path") == "/some/path"

    def test_exists(self, provider, tmp_base):
        import os
        test_file = os.path.join(tmp_base, "test_exists.txt")
        os.makedirs(tmp_base, exist_ok=True)
        with open(test_file, "w") as f:
            f.write("data")
        assert provider.exists(test_file) is True
        assert provider.exists("/nonexistent") is False

    async def test_read(self, provider, tmp_base):
        import uuid
        session_id = uuid.uuid4()
        result = await provider.save(session_id, "test", "read.txt", b"read content", "text/plain")
        content = await provider.read(result["storage_path"])
        assert content == b"read content"

    async def test_get_download_response(self, provider):
        result = await provider.get_download_response("/some/path")
        assert result == {"url": None, "path": "/some/path"}

    def test_provider_name(self, provider):
        assert provider.provider_name == "local"


class TestStorageService:
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock()
        provider.save = AsyncMock(return_value={"storage_path": "/tmp/f.webm", "size": 100, "filename": "f.webm"})
        provider.save_to_path = AsyncMock(return_value={"storage_path": "/tmp/f.txt", "size": 50, "filename": "f.txt", "stored_filename": "abc_f.txt"})
        provider.delete = AsyncMock(return_value=True)
        provider.exists = MagicMock(return_value=True)
        provider.read = AsyncMock(return_value=b"content")
        provider.create_upload = AsyncMock(return_value={"upload_url": "https://example.com/upload", "key": "key", "expires_in": 3600})
        provider.confirm_upload = AsyncMock(return_value={"storage_path": "key", "size": 100})
        provider.get_download_response = AsyncMock(return_value={"url": "https://example.com/dl", "path": None})
        provider.provider_name = "test"
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        from app.core.storage import StorageService
        return StorageService(mock_provider)

    async def test_save_recording(self, service, mock_provider):
        with patch("app.core.storage.validate_uploaded_file") as mock_validate:
            mock_validate.return_value = "audio/webm"
            result = await service.save_recording(uuid.uuid4(), "rec.webm", b"content", "audio/webm")
            assert result["content_type"] is not None

    async def test_save_transcript(self, service, mock_provider):
        with patch("app.core.storage.validate_uploaded_file") as mock_validate:
            mock_validate.return_value = "text/plain"
            result = await service.save_transcript(uuid.uuid4(), "transcript.txt", b"content", "text/plain")
            assert result["content_type"] is not None

    async def test_save_attachment(self, service, mock_provider):
        with patch("app.core.storage.validate_uploaded_file") as mock_validate:
            mock_validate.return_value = "application/pdf"
            import uuid
            result = await service.save_attachment("notes", str(uuid.uuid4()), "file.pdf", b"content", "application/pdf")
            assert result["content_type"] is not None

    async def test_delete_file(self, service, mock_provider):
        result = await service.delete_file("/tmp/f.webm")
        assert result is True
        mock_provider.delete.assert_called_once_with("/tmp/f.webm")

    def test_get_absolute_path(self, service, mock_provider):
        result = service.get_absolute_path("/tmp/f.webm")
        mock_provider.get_absolute_path.assert_called_once_with("/tmp/f.webm")

    def test_exists(self, service, mock_provider):
        result = service.exists("/tmp/f.webm")
        assert result is True
        mock_provider.exists.assert_called_once_with("/tmp/f.webm")

    def test_provider_name(self, service, mock_provider):
        assert service.provider_name == "test"

    async def test_read(self, service, mock_provider):
        result = await service.read("/tmp/f.webm")
        assert result == b"content"

    async def test_create_upload(self, service, mock_provider):
        result = await service.create_upload("key", "application/pdf")
        assert result["upload_url"] == "https://example.com/upload"

    async def test_confirm_upload(self, service, mock_provider):
        result = await service.confirm_upload("key")
        assert result["size"] == 100

    async def test_get_download_response(self, service, mock_provider):
        result = await service.get_download_response("/tmp/f.webm")
        assert result["url"] is not None


# ── LocalStorageProvider — additional coverage ────────────────────────────────

class TestLocalStorageProviderAdditional:
    @pytest.fixture
    def tmp_base(self, tmp_path):
        return str(tmp_path / "storage")

    @pytest.fixture
    def provider(self, tmp_base):
        from app.core.storage import LocalStorageProvider
        return LocalStorageProvider(tmp_base)

    async def test_save_creates_nested_subdirectory(self, provider, tmp_base):
        session_id = uuid.uuid4()
        result = await provider.save(session_id, "transcripts", "tx.txt", b"hello", "text/plain")
        assert os.path.exists(result["storage_path"])

    async def test_save_random_prefix_avoids_collision(self, provider, tmp_base):
        """Two saves of the same filename produce different stored_paths."""
        session_id = uuid.uuid4()
        r1 = await provider.save(session_id, "rec", "same.webm", b"aaa", "audio/webm")
        r2 = await provider.save(session_id, "rec", "same.webm", b"bbb", "audio/webm")
        assert r1["storage_path"] != r2["storage_path"]

    async def test_save_to_path_stored_filename_has_hex_prefix(self, provider):
        result = await provider.save_to_path("notes/123", "doc.pdf", b"pdf", "application/pdf")
        stored = result["stored_filename"]
        parts = stored.split("_", 1)
        assert len(parts) == 2
        assert parts[1] == "doc.pdf"
        assert len(parts[0]) == 8

    async def test_read_raises_for_missing_file(self, provider, tmp_base):
        with pytest.raises(FileNotFoundError):
            await provider.read("/nonexistent/path/file.txt")

    async def test_save_size_matches_content_length(self, provider, tmp_base):
        session_id = uuid.uuid4()
        content = b"exactly 12 bytes"
        result = await provider.save(session_id, "test", "f.bin", content, "application/octet-stream")
        assert result["size"] == len(content)

    async def test_get_download_response_returns_path_as_url_none(self, provider):
        result = await provider.get_download_response("/storage/file.txt")
        assert result["url"] is None
        assert result["path"] == "/storage/file.txt"

    def test_get_absolute_path_passthrough(self, provider):
        p = "/some/absolute/path"
        assert provider.get_absolute_path(p) == p

    def test_exists_false_for_nonexistent(self, provider):
        assert provider.exists("/no/such/file.txt") is False

    async def test_delete_returns_false_for_missing_file(self, provider):
        assert await provider.delete("/no/such/file.txt") is False

    async def test_read_roundtrip(self, provider, tmp_base):
        session_id = uuid.uuid4()
        content = b"roundtrip content"
        result = await provider.save(session_id, "rt", "rt.bin", content, "application/octet-stream")
        read_back = await provider.read(result["storage_path"])
        assert read_back == content


# ── S3StorageProvider — fully mocked AWS ──────────────────────────────────────

class TestS3StorageProvider:
    """All boto3 / aioboto3 calls are mocked. Zero AWS contact."""

    @pytest.fixture
    def mock_boto3_client(self):
        client = MagicMock()
        client.generate_presigned_url = MagicMock(return_value="https://s3.example.com/presigned")
        client.head_object = MagicMock(return_value={})
        return client

    @pytest.fixture
    def provider(self, mock_boto3_client):
        import sys
        mock_boto3 = MagicMock()
        mock_boto3.client = MagicMock(return_value=mock_boto3_client)
        mock_aioboto3 = MagicMock()
        with patch.dict(sys.modules, {"boto3": mock_boto3, "aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as mock_settings:
            mock_settings.AWS_REGION = "us-east-1"
            mock_settings.AWS_ACCESS_KEY_ID = "AKIATEST"
            mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
            mock_settings.AWS_STORAGE_BUCKET_NAME = "test-bucket"
            from app.core.storage import S3StorageProvider as _S3
            p = _S3.__new__(_S3)
            p._client = mock_boto3_client
            p._bucket = "test-bucket"
            return p

    def test_provider_name_is_s3(self, provider):
        assert provider.provider_name == "s3"

    def test_key_format(self, provider):
        session_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        key = provider._key(session_id, "recordings", "file.webm")
        assert str(session_id) in key
        assert "recordings" in key
        assert "file.webm" in key

    def test_key_from_path_format(self, provider):
        key = provider._key_from_path("notes/abc", "doc.pdf")
        assert key == "notes/abc/doc.pdf"

    def test_get_absolute_path_includes_bucket(self, provider):
        path = provider.get_absolute_path("recordings/file.webm")
        assert "s3://" in path
        assert "recordings/file.webm" in path

    def test_exists_returns_true_when_head_object_succeeds(self, provider, mock_boto3_client):
        mock_boto3_client.head_object.return_value = {"ContentLength": 100}
        assert provider.exists("some/key") is True

    def test_exists_returns_false_when_head_object_raises(self, provider, mock_boto3_client):
        mock_boto3_client.head_object.side_effect = Exception("NoSuchKey")
        assert provider.exists("missing/key") is False

    async def test_save_calls_put_object(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.save(uuid.uuid4(), "recordings", "test.webm", b"data", "audio/webm")

        mock_s3.put_object.assert_called_once()
        assert result["size"] == 4
        assert result["filename"] == "test.webm"
        assert "storage_path" in result

    async def test_save_to_path_calls_put_object(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.save_to_path("attachments/tasks", "doc.pdf", b"pdfdata", "application/pdf")

        mock_s3.put_object.assert_called_once()
        assert result["filename"] == "doc.pdf"
        assert result["size"] == len(b"pdfdata")

    async def test_delete_returns_true_on_success(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.delete("recordings/file.webm")

        assert result is True
        mock_s3.delete_object.assert_called_once()

    async def test_delete_returns_false_on_exception(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_s3.delete_object = AsyncMock(side_effect=Exception("S3 error"))
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.delete("bad/key")
        assert result is False

    async def test_read_returns_body_bytes(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_s3.get_object = AsyncMock(return_value={
            "Body": AsyncMock(read=AsyncMock(return_value=b"file content"))
        })
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.read("recordings/file.webm")

        assert result == b"file content"

    async def test_create_upload_returns_presigned_url(self, provider, mock_boto3_client):
        mock_boto3_client.generate_presigned_url.return_value = "https://s3.presigned.url"
        result = await provider.create_upload("recordings/test.webm", "audio/webm")
        assert result["upload_url"] == "https://s3.presigned.url"
        assert result["key"] == "recordings/test.webm"
        assert result["expires_in"] == 3600

    async def test_confirm_upload_returns_size(self, provider):
        import sys
        mock_s3 = AsyncMock()
        mock_s3.head_object = AsyncMock(return_value={"ContentLength": 2048})
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)
        mock_session = MagicMock()
        mock_session.client.return_value = mock_context
        mock_aioboto3 = MagicMock()
        mock_aioboto3.Session.return_value = mock_session

        with patch.dict(sys.modules, {"aioboto3": mock_aioboto3}), \
             patch("app.core.storage.settings") as s:
            s.AWS_ACCESS_KEY_ID = "k"
            s.AWS_SECRET_ACCESS_KEY = "s"
            s.AWS_REGION = "us-east-1"
            result = await provider.confirm_upload("recordings/key.webm")

        assert result["size"] == 2048
        assert result["storage_path"] == "recordings/key.webm"

    async def test_get_download_response_returns_presigned_url(self, provider, mock_boto3_client):
        mock_boto3_client.generate_presigned_url.return_value = "https://s3.dl.url/file"
        result = await provider.get_download_response("recordings/file.webm")
        assert result["url"] == "https://s3.dl.url/file"
        assert result["path"] is None


# ── StorageProvider ABC ────────────────────────────────────────────────────────

class TestStorageProviderABC:
    def test_cannot_instantiate_abstract_provider(self):
        from app.core.storage import StorageProvider
        with pytest.raises(TypeError):
            StorageProvider()  # type: ignore

    async def test_read_raises_not_implemented(self):
        from app.core.storage import StorageProvider
        class MinimalProvider(StorageProvider):
            async def save(self, *a, **kw): return {}
            async def save_to_path(self, *a, **kw): return {}
            async def delete(self, *a, **kw): return True
            def get_absolute_path(self, p): return p
            def exists(self, p): return False
            async def get_download_response(self, p): return {"url": None, "path": p}

        p = MinimalProvider()
        with pytest.raises(NotImplementedError):
            await p.read("/some/path")

    async def test_create_upload_raises_not_implemented(self):
        from app.core.storage import StorageProvider
        class MinimalProvider(StorageProvider):
            async def save(self, *a, **kw): return {}
            async def save_to_path(self, *a, **kw): return {}
            async def delete(self, *a, **kw): return True
            def get_absolute_path(self, p): return p
            def exists(self, p): return False
            async def get_download_response(self, p): return {"url": None, "path": p}

        p = MinimalProvider()
        with pytest.raises(NotImplementedError):
            await p.create_upload("key", "audio/webm")

    async def test_confirm_upload_raises_not_implemented(self):
        from app.core.storage import StorageProvider
        class MinimalProvider(StorageProvider):
            async def save(self, *a, **kw): return {}
            async def save_to_path(self, *a, **kw): return {}
            async def delete(self, *a, **kw): return True
            def get_absolute_path(self, p): return p
            def exists(self, p): return False
            async def get_download_response(self, p): return {"url": None, "path": p}

        p = MinimalProvider()
        with pytest.raises(NotImplementedError):
            await p.confirm_upload("key")


# ── StorageService — additional scenarios ─────────────────────────────────────

class TestStorageServiceAdditional:
    @pytest.fixture
    def mock_provider(self):
        p = MagicMock()
        p.save = AsyncMock(return_value={
            "storage_path": "/tmp/f.webm", "size": 100, "filename": "f.webm"
        })
        p.save_to_path = AsyncMock(return_value={
            "storage_path": "/tmp/f.pdf", "size": 50,
            "filename": "f.pdf", "stored_filename": "abc_f.pdf"
        })
        p.delete = AsyncMock(return_value=True)
        p.exists = MagicMock(return_value=True)
        p.read = AsyncMock(return_value=b"content")
        p.create_upload = AsyncMock(return_value={"upload_url": "https://u", "key": "k", "expires_in": 3600})
        p.confirm_upload = AsyncMock(return_value={"storage_path": "k", "size": 99})
        p.get_download_response = AsyncMock(return_value={"url": "https://dl", "path": None})
        p.provider_name = "test"
        return p

    @pytest.fixture
    def service(self, mock_provider):
        from app.core.storage import StorageService
        return StorageService(mock_provider)

    async def test_save_recording_validation_failure_propagates(self, service):
        from app.modules.attachments.exceptions import AttachmentValidationError
        with patch("app.core.storage.validate_uploaded_file",
                   side_effect=AttachmentValidationError("bad file")):
            with pytest.raises(AttachmentValidationError):
                await service.save_recording(uuid.uuid4(), "bad.webm", b"x", "audio/webm")

    async def test_save_transcript_validation_failure_propagates(self, service):
        from app.modules.attachments.exceptions import AttachmentValidationError
        with patch("app.core.storage.validate_uploaded_file",
                   side_effect=AttachmentValidationError("bad file")):
            with pytest.raises(AttachmentValidationError):
                await service.save_transcript(uuid.uuid4(), "bad.txt", b"x", "text/plain")

    async def test_save_attachment_constructs_relative_dir(self, service, mock_provider):
        entity_id = str(uuid.uuid4())
        with patch("app.core.storage.validate_uploaded_file", return_value="application/pdf"):
            await service.save_attachment("tasks", entity_id, "doc.pdf", b"pdf", "application/pdf")
        call_args = mock_provider.save_to_path.call_args[0]
        assert "tasks" in call_args[0]
        assert entity_id in call_args[0]

    async def test_delete_file_returns_false_propagated(self, service, mock_provider):
        mock_provider.delete = AsyncMock(return_value=False)
        result = await service.delete_file("/tmp/missing.webm")
        assert result is False

    async def test_read_delegates_to_provider(self, service, mock_provider):
        result = await service.read("/tmp/f.webm")
        mock_provider.read.assert_called_once_with("/tmp/f.webm")
        assert result == b"content"

    async def test_save_recording_passes_detected_mime_to_provider(self, service, mock_provider):
        with patch("app.core.storage.validate_uploaded_file", return_value="audio/webm"):
            await service.save_recording(uuid.uuid4(), "rec.webm", b"data", "audio/webm")
        _, _, _, _, passed_mime = mock_provider.save.call_args[0]
        assert passed_mime == "audio/webm"

    async def test_save_transcript_passes_detected_mime_to_provider(self, service, mock_provider):
        with patch("app.core.storage.validate_uploaded_file", return_value="text/plain"):
            await service.save_transcript(uuid.uuid4(), "tx.txt", b"data", "text/plain")
        _, _, _, _, passed_mime = mock_provider.save.call_args[0]
        assert passed_mime == "text/plain"

    async def test_create_upload_delegates(self, service, mock_provider):
        result = await service.create_upload("mykey", "audio/webm")
        mock_provider.create_upload.assert_called_once_with("mykey", "audio/webm")
        assert result["upload_url"] == "https://u"

    async def test_confirm_upload_delegates(self, service, mock_provider):
        result = await service.confirm_upload("mykey")
        mock_provider.confirm_upload.assert_called_once_with("mykey")
        assert result["size"] == 99

    async def test_get_download_response_delegates(self, service, mock_provider):
        result = await service.get_download_response("/tmp/f.webm")
        mock_provider.get_download_response.assert_called_once_with("/tmp/f.webm")
        assert result["url"] == "https://dl"
