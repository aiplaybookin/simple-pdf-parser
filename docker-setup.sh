#!/bin/bash

# Docker Setup Script for Intelligent Document Processing Application
# This script helps you set up and run the application with Docker

set -e

echo "🚀 Intelligent Document Processing - Docker Setup"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GOOGLE_API_KEY"
    echo ""
    read -p "Press Enter to open .env file in default editor, or Ctrl+C to exit..."
    ${EDITOR:-nano} .env
    echo ""
fi

# Verify GOOGLE_API_KEY is set
if grep -q "your_api_key_here" .env; then
    echo "⚠️  WARNING: GOOGLE_API_KEY is not set in .env file"
    echo "   Please update .env file with your actual API key"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Access Points:"
echo "   Frontend:  http://localhost:3000"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose stop"
echo "   Restart services: docker-compose restart"
echo "   Remove all:       docker-compose down -v"
echo ""
echo "📚 For more information, see DOCKER.md"
