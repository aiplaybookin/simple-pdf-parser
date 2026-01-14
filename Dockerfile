# Backend Dockerfile for FastAPI application
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy all necessary files for installation
COPY pyproject.toml ./
COPY README.md ./
COPY app/ ./app/
COPY worker.py ./

# Install Python dependencies
RUN uv pip install --system -e .

# Create logs directory
RUN mkdir -p logs

# Expose port for FastAPI
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
