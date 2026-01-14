"""Pydantic models for request/response validation."""
from typing import List, Literal, Dict, Optional
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Information about a processed file."""
    filename: str
    md_filename: str
    status: str
    size: int


class FailedFileInfo(BaseModel):
    """Information about a failed file."""
    filename: str
    status: str = "failed"
    error: str


class UploadResponse(BaseModel):
    """Response after uploading files."""
    task_id: str
    status: str = "queued"
    message: str
    files: List[str]
    mode: Literal["gemini", "pypdf"]
    endpoints: Dict[str, str]


class TaskStatusPending(BaseModel):
    """Task status when pending."""
    task_id: str
    state: str
    status: str
    message: str
    current: int = 0
    total: int


class TaskStatusProcessing(BaseModel):
    """Task status when processing."""
    task_id: str
    state: str
    status: str
    message: str
    current: int
    total: int
    processed: List[FileInfo] = Field(default_factory=list)
    failed: List[FailedFileInfo] = Field(default_factory=list)


class TaskStatusSuccess(BaseModel):
    """Task status when completed successfully."""
    task_id: str
    state: str
    status: str
    message: str
    total: int
    processed: int
    failed: int
    files: List[FileInfo]
    errors: List[FailedFileInfo] = Field(default_factory=list)
    mode: str
    download_url: Optional[str] = None


class TaskStatusFailure(BaseModel):
    """Task status when failed."""
    task_id: str
    state: str
    status: str
    error: str


class DownloadResponse(BaseModel):
    """Response with summaries and download links."""
    task_id: str
    summaries: Dict[str, str] = Field(
        description="Mapping of filename to AI-generated summary"
    )
    files: List[FileInfo]
    markdown_download_endpoint: str


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    redis: str


class RootResponse(BaseModel):
    """Root endpoint response."""
    message: str
    status: str
    version: str
    features: List[str]
    endpoints: Dict[str, str]
    worker: Dict[str, str]
