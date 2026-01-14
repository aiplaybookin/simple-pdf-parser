"""API endpoints."""
import io
import json
import uuid
import base64
import zipfile
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from redis.asyncio import Redis

from app.models.schemas import (
    UploadResponse,
    DownloadResponse,
    HealthCheckResponse,
    RootResponse
)
from app.config import settings
from app.logging_config import get_logger
from app.exceptions import (
    RedisConnectionError,
    TaskNotFoundError,
    TaskNotCompleteError,
    InvalidFileError,
    ProcessingError
)

logger = get_logger(__name__)

router = APIRouter()

# Global Redis client (will be set from main.py)
redis_client: Optional[Redis] = None


def set_redis_client(client: Redis) -> None:
    """Set the Redis client instance."""
    global redis_client
    redis_client = client


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    mode: str = Form(...)
):
    """
    Upload one or more PDF files for async processing.
    Returns task_id immediately for polling.

    Args:
        files: List of PDF files to process
        mode: Parsing mode - "gemini" or "pypdf"

    Returns:
        JSON with task_id for status polling
    """
    logger.info(f"Upload request received: {len(files)} files, mode={mode}")

    if mode not in ["gemini", "pypdf"]:
        logger.warning(f"Invalid mode requested: {mode}")
        raise HTTPException(
            status_code=400,
            detail="Mode must be either 'gemini' or 'pypdf'"
        )

    if not files:
        logger.warning("Upload attempted with no files")
        raise HTTPException(
            status_code=400,
            detail="No files provided. Please upload at least one PDF file."
        )

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Non-PDF file upload attempted: {file.filename}")
            raise InvalidFileError(
                filename=file.filename,
                reason="Only PDF files are accepted"
            )

    if not redis_client:
        logger.error("Redis connection not available for upload")
        raise RedisConnectionError(
            "Unable to process upload. Please try again later."
        )

    # Generate unique task ID
    task_id = str(uuid.uuid4())
    logger.info(f"Generated task_id: {task_id}")

    # Prepare files data
    files_data = []
    total_size = 0
    for file in files:
        content = await file.read()
        file_size = len(content)
        total_size += file_size
        files_data.append({
            'filename': file.filename,
            'content': base64.b64encode(content).decode('utf-8')
        })
        logger.debug(f"Read file {file.filename}: {file_size} bytes")

    logger.info(f"Total upload size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")

    # Add task to Redis Stream
    task_message = {
        'task_id': task_id,
        'mode': mode,
        'files_data': json.dumps(files_data)
    }

    message_id = await redis_client.xadd(settings.STREAM_NAME, task_message)
    logger.info(f"Task {task_id} added to Redis Stream with message_id: {message_id}")

    # Initialize task status
    await redis_client.set(
        f"task:{task_id}:status",
        json.dumps({
            "status": "PENDING",
            "message": "Task queued for processing",
            "total": len(files),
            "current": 0
        }),
        ex=settings.TASK_EXPIRATION
    )

    logger.info(f"Task {task_id} initialized - {len(files)} files, mode={mode}")

    return UploadResponse(
        task_id=task_id,
        status="queued",
        message=f"Processing {len(files)} file(s) in background",
        files=[f['filename'] for f in files_data],
        mode=mode,
        endpoints={
            "status": f"/status/{task_id}",
            "download": f"/download/{task_id}"
        }
    )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> JSONResponse:
    """
    Get the status of a processing task.

    Args:
        task_id: The task ID returned from upload

    Returns:
        JSON with task status and progress
    """
    logger.debug(f"Status check requested for task: {task_id}")

    if not redis_client:
        logger.error("Redis connection not available for status check")
        raise RedisConnectionError(
            "Unable to check task status. Please try again later."
        )

    status_key = f"task:{task_id}:status"
    status_json = await redis_client.get(status_key)

    if not status_json:
        logger.warning(f"Task {task_id} not found or expired")
        raise TaskNotFoundError(task_id)

    status_data = json.loads(status_json)
    current_status = status_data.get('status', 'UNKNOWN')

    logger.info(f"Task {task_id} status: {current_status}")

    # Build response without including files/errors data (only summary counts)
    response = {
        'task_id': task_id,
        'state': current_status,
        'status': current_status,
        'message': status_data.get('message', ''),
        'total': status_data.get('total', 0),
        'current': status_data.get('current', 0)
    }

    # Add processed/failed counts for SUCCESS state
    if current_status == 'SUCCESS':
        response['processed'] = status_data.get('processed', 0)
        response['failed'] = status_data.get('failed', 0)
        response['mode'] = status_data.get('mode', '')
        response['download_url'] = f"/download/{task_id}"
        logger.info(f"Task {task_id} completed successfully")
    elif current_status == 'PROCESSING':
        # Include in-progress file lists for processing state
        response['processed'] = status_data.get('processed', [])
        response['failed'] = status_data.get('failed', [])
    elif current_status == 'FAILURE':
        response['error'] = status_data.get('error', 'Unknown error')

    return JSONResponse(content=response)


@router.get("/download/{task_id}", response_model=DownloadResponse)
async def download_results(task_id: str):
    """
    Get summaries and download links for processed documents.

    Args:
        task_id: The task ID returned from upload

    Returns:
        JSON with summaries for each file (filename as key, summary as value)
    """
    logger.info(f"Download request for task: {task_id}")

    if not redis_client:
        logger.error("Redis connection not available for download")
        raise RedisConnectionError(
            "Unable to retrieve results. Please try again later."
        )

    # Check task status
    status_key = f"task:{task_id}:status"
    status_json = await redis_client.get(status_key)

    if not status_json:
        raise TaskNotFoundError(task_id)

    status_data = json.loads(status_json)

    if status_data.get('status') != 'SUCCESS':
        raise TaskNotCompleteError(
            task_id=task_id,
            current_state=status_data.get('status', 'UNKNOWN')
        )

    processed_files = status_data.get('files', [])

    if not processed_files:
        logger.error(f"No processed files found for task {task_id}")
        raise ProcessingError(
            message="No processed files found",
            task_id=task_id
        )

    # Retrieve summaries from Redis
    summaries = {}
    for file_info in processed_files:
        filename = file_info['filename']
        summary_key = f"task:{task_id}:summary:{filename}"

        summary = await redis_client.get(summary_key)
        if summary:
            summaries[filename] = summary
            logger.debug(f"Retrieved summary for {filename}: {len(summary)} chars")
        else:
            summaries[filename] = "Summary not available"
            logger.warning(f"Summary not available for {filename}")

    logger.info(f"Returning summaries for task {task_id}: {len(summaries)} files")

    return DownloadResponse(
        task_id=task_id,
        summaries=summaries,
        files=processed_files,
        markdown_download_endpoint=f"/download-markdown/{task_id}"
    )


@router.get("/download-markdown/{task_id}")
async def download_markdown_files(task_id: str) -> StreamingResponse:
    """
    Download the actual markdown files for a completed task.

    Args:
        task_id: The task ID returned from upload

    Returns:
        Single markdown file or ZIP file with all processed documents
    """
    logger.info(f"Markdown download request for task: {task_id}")

    if not redis_client:
        raise RedisConnectionError(
            "Unable to retrieve markdown files. Please try again later."
        )

    # Check task status
    status_key = f"task:{task_id}:status"
    status_json = await redis_client.get(status_key)

    if not status_json:
        raise TaskNotFoundError(task_id)

    status_data = json.loads(status_json)

    if status_data.get('status') != 'SUCCESS':
        raise TaskNotCompleteError(
            task_id=task_id,
            current_state=status_data.get('status', 'UNKNOWN')
        )

    processed_files = status_data.get('files', [])

    if not processed_files:
        logger.error(f"No processed files found for task {task_id}")
        raise ProcessingError(
            message="No processed files found",
            task_id=task_id
        )

    # Retrieve markdown files from Redis
    markdown_files = {}
    for file_info in processed_files:
        md_filename = file_info['md_filename']
        redis_key = f"task:{task_id}:file:{md_filename}"

        markdown_content = await redis_client.get(redis_key)
        if markdown_content:
            markdown_files[md_filename] = markdown_content

    if not markdown_files:
        logger.error(f"Markdown files not found or expired for task {task_id}")
        raise ProcessingError(
            message="Processed files have expired or not found in Redis",
            task_id=task_id
        )

    # Return single file or ZIP
    if len(markdown_files) == 1:
        md_filename, markdown_content = list(markdown_files.items())[0]
        logger.info(f"Returning single markdown file: {md_filename}")
        return StreamingResponse(
            io.BytesIO(markdown_content.encode('utf-8')),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={md_filename}"
            }
        )
    else:
        logger.info(f"Creating ZIP with {len(markdown_files)} markdown files")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for md_filename, markdown_content in markdown_files.items():
                zip_file.writestr(md_filename, markdown_content)

        zip_buffer.seek(0)
        logger.info(f"Returning ZIP file with {len(markdown_files)} files")
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=task_{task_id}_results.zip"
            }
        )


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """API health check and documentation."""
    return RootResponse(
        message="Intelligent Document Processing API with AI Summarization",
        status="running",
        version="3.0 - Redis Streams + AI Summary",
        features=[
            "PDF to Markdown conversion (Gemini or PyPDF)",
            "AI-powered summarization with chunked processing",
            "Async task queue with Redis Streams",
            "Support for large documents (5000 word chunks)"
        ],
        endpoints={
            "upload": "/upload (POST) - Upload PDFs, returns task_id",
            "status": "/status/{task_id} (GET) - Check task progress & summarization",
            "download": "/download/{task_id} (GET) - Get summaries as JSON",
            "download_markdown": "/download-markdown/{task_id} (GET) - Download markdown files",
            "health": "/health (GET) - Health check",
            "docs": "/docs - Interactive API documentation"
        },
        worker={
            "start": "python worker.py"
        }
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring."""
    logger.debug("Health check requested")

    if not redis_client:
        logger.error("Health check failed: Redis not connected")
        raise RedisConnectionError("Redis not connected")

    try:
        await redis_client.ping()
        logger.debug("Health check passed: Redis connected")
        return HealthCheckResponse(status="healthy", redis="connected")
    except Exception as e:
        logger.error(f"Health check failed: Redis error - {str(e)}")
        raise RedisConnectionError(f"Redis error: {str(e)}")
