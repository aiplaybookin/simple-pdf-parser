"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
import json

from app.main import create_app
from app.routes import api


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.xadd = AsyncMock(return_value=b'1234567890-0')
    mock.set = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.close = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def client(mock_redis):
    """Async test client with mocked Redis."""
    app = create_app()

    # Override the lifespan to use mock Redis
    api.set_redis_client(mock_redis)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_pdf_content():
    """Sample PDF file content."""
    # Minimal valid PDF
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"


@pytest.fixture
def task_id():
    """Sample task ID."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def pending_task_status(task_id):
    """Sample pending task status."""
    return json.dumps({
        "status": "PENDING",
        "message": "Task queued for processing",
        "total": 1,
        "current": 0
    })


@pytest.fixture
def processing_task_status(task_id):
    """Sample processing task status."""
    return json.dumps({
        "status": "PROCESSING",
        "message": "Processing document.pdf...",
        "total": 1,
        "current": 1,
        "processed": [],
        "failed": []
    })


@pytest.fixture
def success_task_status(task_id):
    """Sample successful task status."""
    return json.dumps({
        "status": "SUCCESS",
        "message": "Processing complete",
        "total": 1,
        "processed": 1,
        "failed": 0,
        "files": [
            {
                "filename": "document.pdf",
                "md_filename": "document.md",
                "status": "success",
                "size": 1234,
                "summary": "Test summary"
            }
        ],
        "errors": [],
        "mode": "pypdf"
    })


@pytest.fixture
def failure_task_status(task_id):
    """Sample failed task status."""
    return json.dumps({
        "status": "FAILURE",
        "error": "Processing failed",
        "message": "Task failed: Processing failed"
    })
