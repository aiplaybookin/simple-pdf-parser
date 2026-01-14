"""API endpoint tests."""
import pytest
import json
import io
from unittest.mock import AsyncMock


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
        assert "features" in data
        assert "endpoints" in data


class TestHealthCheckEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, client, mock_redis):
        """Test health check when Redis is connected."""
        mock_redis.ping = AsyncMock(return_value=True)
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis"] == "connected"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client, mock_redis):
        """Test health check when Redis fails."""
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        response = await client.get("/health")
        assert response.status_code == 503


class TestUploadEndpoint:
    """Tests for upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_single_pdf_pypdf(self, client, mock_redis, sample_pdf_content):
        """Test uploading single PDF with PyPDF mode."""
        files = {
            "files": ("test.pdf", sample_pdf_content, "application/pdf")
        }
        data = {"mode": "pypdf"}

        response = await client.post("/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert "task_id" in result
        assert result["status"] == "queued"
        assert result["mode"] == "pypdf"
        assert len(result["files"]) == 1
        assert result["files"][0] == "test.pdf"
        assert "endpoints" in result

    @pytest.mark.asyncio
    async def test_upload_multiple_pdfs_gemini(self, client, mock_redis, sample_pdf_content):
        """Test uploading multiple PDFs with Gemini mode."""
        files = [
            ("files", ("test1.pdf", sample_pdf_content, "application/pdf")),
            ("files", ("test2.pdf", sample_pdf_content, "application/pdf"))
        ]
        data = {"mode": "gemini"}

        response = await client.post("/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["mode"] == "gemini"
        assert len(result["files"]) == 2

    @pytest.mark.asyncio
    async def test_upload_invalid_mode(self, client, sample_pdf_content):
        """Test upload with invalid mode."""
        files = {
            "files": ("test.pdf", sample_pdf_content, "application/pdf")
        }
        data = {"mode": "invalid"}

        response = await client.post("/upload", files=files, data=data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_non_pdf_file(self, client):
        """Test upload with non-PDF file."""
        files = {
            "files": ("test.txt", b"Hello World", "text/plain")
        }
        data = {"mode": "pypdf"}

        response = await client.post("/upload", files=files, data=data)
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["success"] is False
        assert "PDF" in error_data["error"]["message"]

    @pytest.mark.asyncio
    async def test_upload_no_files(self, client):
        """Test upload with no files."""
        data = {"mode": "pypdf"}
        response = await client.post("/upload", data=data)
        assert response.status_code == 422  # FastAPI validation error


class TestStatusEndpoint:
    """Tests for status endpoint."""

    @pytest.mark.asyncio
    async def test_status_pending(self, client, mock_redis, task_id, pending_task_status):
        """Test status endpoint for pending task."""
        mock_redis.get = AsyncMock(return_value=pending_task_status)

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "PENDING"
        assert data["current"] == 0

    @pytest.mark.asyncio
    async def test_status_processing(self, client, mock_redis, task_id, processing_task_status):
        """Test status endpoint for processing task."""
        mock_redis.get = AsyncMock(return_value=processing_task_status)

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "PROCESSING"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_status_success(self, client, mock_redis, task_id, success_task_status):
        """Test status endpoint for successful task."""
        mock_redis.get = AsyncMock(return_value=success_task_status)

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "SUCCESS"
        assert "download_url" in data

    @pytest.mark.asyncio
    async def test_status_not_found(self, client, mock_redis, task_id):
        """Test status endpoint for non-existent task."""
        mock_redis.get = AsyncMock(return_value=None)

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["success"] is False
        assert "not found" in error_data["error"]["message"]


class TestDownloadEndpoint:
    """Tests for download endpoint."""

    @pytest.mark.asyncio
    async def test_download_success(self, client, mock_redis, task_id, success_task_status):
        """Test download endpoint for successful task."""
        mock_redis.get = AsyncMock(side_effect=[
            success_task_status,  # status check
            "Test summary for document.pdf"  # summary
        ])

        response = await client.get(f"/download/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        assert "document.pdf" in data["summaries"]
        assert "markdown_download_endpoint" in data

    @pytest.mark.asyncio
    async def test_download_task_not_complete(
        self, client, mock_redis, task_id, pending_task_status
    ):
        """Test download when task is not complete."""
        mock_redis.get = AsyncMock(return_value=pending_task_status)

        response = await client.get(f"/download/{task_id}")
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["success"] is False
        assert "not complete" in error_data["error"]["message"]

    @pytest.mark.asyncio
    async def test_download_task_not_found(self, client, mock_redis, task_id):
        """Test download for non-existent task."""
        mock_redis.get = AsyncMock(return_value=None)

        response = await client.get(f"/download/{task_id}")
        assert response.status_code == 404


class TestDownloadMarkdownEndpoint:
    """Tests for download markdown endpoint."""

    @pytest.mark.asyncio
    async def test_download_markdown_single_file(
        self, client, mock_redis, task_id, success_task_status
    ):
        """Test downloading single markdown file."""
        mock_redis.get = AsyncMock(side_effect=[
            success_task_status,  # status check
            "# Test Document\n\nContent here"  # markdown content
        ])

        response = await client.get(f"/download-markdown/{task_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_download_markdown_multiple_files(
        self, client, mock_redis, task_id
    ):
        """Test downloading multiple markdown files as ZIP."""
        success_status_multi = json.dumps({
            "status": "SUCCESS",
            "files": [
                {"filename": "doc1.pdf", "md_filename": "doc1.md", "status": "success", "size": 100},
                {"filename": "doc2.pdf", "md_filename": "doc2.md", "status": "success", "size": 200}
            ]
        })

        mock_redis.get = AsyncMock(side_effect=[
            success_status_multi,  # status check
            "# Doc 1",  # doc1.md
            "# Doc 2"   # doc2.md
        ])

        response = await client.get(f"/download-markdown/{task_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    @pytest.mark.asyncio
    async def test_download_markdown_expired_files(
        self, client, mock_redis, task_id, success_task_status
    ):
        """Test download when markdown files have expired."""
        mock_redis.get = AsyncMock(side_effect=[
            success_task_status,  # status check
            None  # expired markdown
        ])

        response = await client.get(f"/download-markdown/{task_id}")
        assert response.status_code == 500
        error_data = response.json()
        assert error_data["success"] is False
        assert "expired" in error_data["error"]["message"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_redis_unavailable_on_upload(self, client, sample_pdf_content):
        """Test upload when Redis is unavailable."""
        from app.routes import api
        api.set_redis_client(None)

        files = {
            "files": ("test.pdf", sample_pdf_content, "application/pdf")
        }
        data = {"mode": "pypdf"}

        response = await client.post("/upload", files=files, data=data)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_large_file_upload(self, client, mock_redis):
        """Test uploading large PDF file."""
        large_content = b"%PDF-1.4\n" + b"A" * (10 * 1024 * 1024)  # 10MB
        files = {
            "files": ("large.pdf", large_content, "application/pdf")
        }
        data = {"mode": "pypdf"}

        response = await client.post("/upload", files=files, data=data)
        # Should succeed or fail gracefully
        assert response.status_code in [200, 413, 422]

    @pytest.mark.asyncio
    async def test_invalid_task_id_format(self, client, mock_redis):
        """Test status with invalid task ID format."""
        mock_redis.get = AsyncMock(return_value=None)

        response = await client.get("/status/invalid-id")
        assert response.status_code == 404
