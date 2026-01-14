#!/bin/bash
# Start Redis Streams worker for document processing

echo "Starting Redis Streams worker..."
echo "Make sure Redis is running on localhost:6379"
echo ""

python worker.py
