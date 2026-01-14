#!/bin/bash
# Run the FastAPI application

echo "Starting Intelligent Document Processing API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
