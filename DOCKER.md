# Docker Deployment Guide

Complete guide for running the Intelligent Document Processing application with Docker.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- At least 2GB of free RAM
- Google Gemini API key ([Get API key](https://makersuite.google.com/app/apikey))

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /path/to/simple-pdf-parser

# Create .env file from example
cp .env.example .env

# Edit .env and add your Google API key
nano .env  # or use your preferred editor
```

### 2. Configure Environment

Edit `.env` file:

```bash
GOOGLE_API_KEY=your_actual_api_key_here
REDIS_URL=redis://redis:6379/0
CHUNK_SIZE=5000
WORKER_NAME=worker_1
```

### 3. Start All Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Access the Application

Once all services are running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

## Architecture

The Docker setup includes 4 services:

```
┌─────────────────────────────────────────────┐
│  Frontend (React + Nginx) - Port 3000      │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  API (FastAPI) - Port 8000                  │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  Redis (Message Queue) - Port 6379          │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  Worker (Background Processing)             │
└─────────────────────────────────────────────┘
```

### Service Details

**1. Redis (simple-pdf-parser-redis)**

- Message queue and cache
- Stores task status and results
- Data persisted in Docker volume

**2. API (simple-pdf-parser-api)**

- FastAPI application
- Handles HTTP requests
- Manages task queue
- Health check endpoint: `/health`

**3. Worker (simple-pdf-parser-worker)**

- Processes PDF files
- Generates AI summaries
- Runs in background
- Can scale horizontally

**4. Frontend (simple-pdf-parser-frontend)**

- React single-page application
- Served by Nginx
- Proxies API requests
- Optimized static assets

## Docker Commands

### Starting Services

```bash
# Start all services in background
docker-compose up -d

# Start specific service
docker-compose up -d api

# Start with rebuild
docker-compose up -d --build

# View startup logs
docker-compose logs -f
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 api

# Since specific time
docker-compose logs --since 10m worker
```

### Service Management

```bash
# Check service status
docker-compose ps

# Restart specific service
docker-compose restart api

# Rebuild specific service
docker-compose build api
docker-compose up -d api

# Scale workers
docker-compose up -d --scale worker=3
```

### Debugging

```bash
# Execute command in running container
docker-compose exec api bash
docker-compose exec worker python --version

# View container resource usage
docker stats

# Inspect service configuration
docker-compose config

# View service health
docker inspect simple-pdf-parser-api | grep -A 10 Health
```

## Development with Docker

### Hot Reload (Development Mode)

For development with hot reload, use volume mounts:

```yaml
# Add to docker-compose.override.yml
version: "3.8"
services:
  api:
    volumes:
      - ./app:/app/app
      - ./worker.py:/app/worker.py
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    volumes:
      - ./app:/app/app
      - ./worker.py:/app/worker.py
```

```bash
# Start with override
docker-compose up -d
```

### Running Tests in Docker

```bash
# Run tests in API container
docker-compose exec api pytest tests/ -v

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=term-missing

# Run specific test
docker-compose exec api pytest tests/test_api.py::TestUploadEndpoint
```

## Production Deployment

### Build for Production

```bash
# Build production images
docker-compose build --no-cache

# Tag images for registry
docker tag simple-pdf-parser-api:latest your-registry.com/simple-pdf-parser-api:1.0.0
docker tag simple-pdf-parser-frontend:latest your-registry.com/simple-pdf-parser-frontend:1.0.0

# Push to registry
docker push your-registry.com/simple-pdf-parser-api:1.0.0
docker push your-registry.com/simple-pdf-parser-frontend:1.0.0
```

### Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"
services:
  api:
    image: your-registry.com/simple-pdf-parser-api:1.0.0
    environment:
      - LOG_LEVEL=INFO
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 1G

  worker:
    image: your-registry.com/simple-pdf-parser-api:1.0.0
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "2"
          memory: 2G

  frontend:
    image: your-registry.com/simple-pdf-parser-frontend:1.0.0
    deploy:
      replicas: 2
```

```bash
# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables (Production)

```bash
# Production .env
GOOGLE_API_KEY=prod_api_key_here
REDIS_URL=redis://redis:6379/0
CHUNK_SIZE=5000
WORKER_NAME=prod_worker
LOG_LEVEL=INFO
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000/health

# Check Redis
docker-compose exec redis redis-cli ping
```

### Resource Monitoring

```bash
# Real-time resource usage
docker stats

# Service-specific stats
docker stats simple-pdf-parser-api simple-pdf-parser-worker

# Memory usage
docker-compose exec api free -h

# Disk usage
docker system df
```

### Logs Analysis

```bash
# Search for errors
docker-compose logs api | grep ERROR

# Count requests
docker-compose logs api | grep "POST /upload" | wc -l

# Export logs
docker-compose logs --no-color api > api.log
```

## Troubleshooting

### Common Issues

**1. Port Already in Use**

```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

**2. Redis Connection Failed**

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

**3. API Not Responding**

```bash
# Check API logs
docker-compose logs api

# Check if API is running
docker-compose ps api

# Restart API
docker-compose restart api

# Check health endpoint
curl http://localhost:8000/health
```

**4. Worker Not Processing**

```bash
# Check worker logs
docker-compose logs worker

# Check if worker is running
docker-compose ps worker

# Verify Redis stream
docker-compose exec redis redis-cli XINFO STREAM pdf_processing_tasks

# Restart worker
docker-compose restart worker
```

**5. Frontend Not Loading**

```bash
# Check frontend logs
docker-compose logs frontend

# Check nginx configuration
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Check if files are built
docker-compose exec frontend ls -la /usr/share/nginx/html
```

**6. Out of Memory**

```bash
# Check memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > 4GB+

# Limit container memory
docker-compose up -d --scale worker=1
```

### Clean Up

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Complete cleanup (WARNING: removes all data)
docker-compose down -v
docker system prune -a --volumes
```

## Data Persistence

### Volumes

```bash
# List volumes
docker volume ls

# Inspect Redis volume
docker volume inspect simple-pdf-parser_redis-data

# Backup Redis data
docker run --rm -v simple-pdf-parser_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Restore Redis data
docker run --rm -v simple-pdf-parser_redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

### Logs Persistence

Logs are stored in `./logs` directory (mounted volume):

```bash
# View logs
ls -la logs/

# Backup logs
tar czf logs-backup.tar.gz logs/
```

## Scaling

### Horizontal Scaling

```bash
# Scale workers to 3 instances
docker-compose up -d --scale worker=3

# Scale API to 2 instances (requires load balancer)
docker-compose up -d --scale api=2

# Check scaled services
docker-compose ps
```

### Load Balancing (Production)

For production, use nginx or HAProxy:

```yaml
# nginx.conf for load balancing
upstream api_backend {
server api_1:8000;
server api_2:8000;
}

server {
location /api {
proxy_pass http://api_backend;
}
}
```

## Security Best Practices

1. **Never commit `.env` file**
2. **Use secrets management** (Docker Secrets, Vault)
3. **Run containers as non-root** (add USER directive in Dockerfile)
4. **Keep images updated** (`docker-compose pull`)
5. **Scan images for vulnerabilities** (`docker scan`)
6. **Use specific image versions** (not `latest`)
7. **Limit container resources**
8. **Use private registry** for production images

## Performance Optimization

### Image Size Reduction

```bash
# Check image sizes
docker images | grep simple-pdf-parser

# Use multi-stage builds (already implemented)
# Use alpine base images
# Remove build dependencies
```

### Build Cache

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose build

# Clear build cache
docker builder prune
```

### Network Optimization

```bash
# Use bridge network (already configured)
# Minimize inter-container communication
# Use local DNS resolution
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Check service status: `docker-compose ps`
3. Review this documentation
4. Check application logs in `./logs/` directory
