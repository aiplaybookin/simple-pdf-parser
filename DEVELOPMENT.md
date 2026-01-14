# Development Guide

## Project Structure

```
simple-pdf-parser/
├── app/                        # Backend API
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration settings
│   ├── logging_config.py       # Logging configuration
│   ├── middleware.py           # Request/Response logging middleware
│   ├── exceptions.py           # Custom exceptions and handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py              # API endpoints
│   └── services/
│       ├── __init__.py
│       └── redis_service.py    # Redis operations
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── Upload.jsx      # File upload component
│   │   │   ├── Processing.jsx  # Progress tracking component
│   │   │   ├── Results.jsx     # Results display component
│   │   │   └── ErrorDisplay.jsx # Error handling component
│   │   ├── App.jsx             # Main app component
│   │   ├── main.jsx            # Entry point
│   │   └── index.css           # Global styles
│   ├── public/                 # Static assets
│   ├── package.json            # Node dependencies
│   └── README.md               # Frontend documentation
├── tests/                      # Backend tests
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── test_api.py             # API tests
├── logs/                       # Application logs (gitignored)
├── worker.py                   # Redis Streams worker
├── pyproject.toml              # Python dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                   # Main documentation
```

## Setup for Development

### 1. Install Dependencies

**Backend:**

```bash
# Install main dependencies
uv pip install -e .

# Install development dependencies (includes pytest, pytest-cov, etc.)
uv pip install -e ".[dev]"
```

**Frontend:**

```bash
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

Create `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379/0
CHUNK_SIZE=5000
```

### 3. Start Services

**Terminal 1: Redis**

```bash
redis-server
```

**Terminal 2: Worker**

```bash
python worker.py
```

**Terminal 3: Backend API Server**

```bash
# Option 1: Using run script
./run.sh

# Option 2: Using uvicorn directly
python -m uvicorn app.main:app --reload

# Option 3: Using Python
python -m app.main
```

**Terminal 4: Frontend Dev Server** (Optional)

```bash
cd frontend
npm run dev
```

### Access Points

Once all services are running:

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend UI**: http://localhost:5173
- **Redis**: localhost:6379

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### View Coverage Report

```bash
# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestUploadEndpoint

# Run specific test method
pytest tests/test_api.py::TestUploadEndpoint::test_upload_single_pdf_pypdf

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Coverage Goals

- **Minimum**: 80% coverage (enforced)
- **Target**: 90% coverage
- Focus on:
  - All API endpoints
  - Error handling
  - Edge cases
  - Integration points

## Frontend Development

### Tech Stack

- **React 18**: Modern React with Hooks
- **Vite**: Fast dev server and build tool
- **CSS3**: Custom styling with animations

### Project Structure

```
frontend/src/
├── components/
│   ├── Upload.jsx          # File upload with drag & drop
│   ├── Upload.css          # Upload component styles
│   ├── Processing.jsx      # Progress tracking & polling
│   ├── Processing.css      # Processing component styles
│   ├── Results.jsx         # Results display & downloads
│   ├── Results.css         # Results component styles
│   ├── ErrorDisplay.jsx    # Error handling
│   └── ErrorDisplay.css    # Error component styles
├── App.jsx                 # Main app component
├── App.css                 # Global app styles
├── main.jsx                # Application entry point
└── index.css               # CSS reset & global styles
```

### Development Commands

```bash
# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Component Overview

**Upload Component:**

- Drag & drop file interface
- Multi-file selection
- PDF validation
- Processing mode selector (PyPDF vs Gemini)

**Processing Component:**

- Real-time status polling (2-second intervals)
- Animated progress bar
- Step-by-step progress visualization
- File-by-file status tracking

**Results Component:**

- Expandable summary cards
- AI-generated summaries display
- Bulk download (ZIP) or individual files
- "Process More" functionality

**ErrorDisplay Component:**

- User-friendly error messages
- Retry functionality
- Automatic error logging

### API Integration

Frontend connects to backend at `http://localhost:8000`.

Key API calls:

- **POST /upload**: Upload files, get task_id
- **GET /status/{task_id}**: Poll task status
- **GET /download/{task_id}**: Get summaries JSON
- **GET /download-markdown/{task_id}**: Download markdown files

### State Management

Using React Hooks:

- `useState`: Component state
- `useEffect`: API polling & lifecycle
- `useRef`: File input reference

### Styling Approach

- **CSS Modules**: Component-scoped styles
- **CSS Variables**: Consistent theming
- **Animations**: Smooth transitions
- **Responsive**: Mobile-first design

### Frontend Workflow

1. **Make Changes**: Edit components in `frontend/src/`
2. **Hot Reload**: Vite automatically reloads changes
3. **Test Locally**: Use frontend with running backend
4. **Build**: Run `npm run build` for production

### Troubleshooting Frontend

**CORS Errors:**

```
Ensure backend CORS middleware allows http://localhost:5173
Check app/main.py lines 76-83
```

**API Not Responding:**

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check if worker is processing
ps aux | grep worker.py
```

**Build Errors:**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Port Already in Use:**

```bash
# Kill process using port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

## Code Organization

### app/main.py

- FastAPI application factory
- Lifespan management (startup/shutdown)
- Redis connection setup
- CORS middleware configuration
- Router registration

### app/config.py

- Environment variable loading
- Configuration constants
- Settings class

### app/models/schemas.py

- Pydantic models for request validation
- Response models
- Type definitions

### app/routes/api.py

- API endpoint definitions with type hints
- Request handlers
- Response formatting
- Custom exception usage

### app/exceptions.py

- Custom exception classes (ApplicationException, RedisConnectionError, etc.)
- Exception handlers for consistent error responses
- User-friendly error messages
- Validation error formatting

### app/middleware.py

- LoggingMiddleware: Logs all requests/responses with timing
- ErrorLoggingMiddleware: Catches and logs unhandled exceptions
- Request ID tracking

### app/services/

- Business logic separated from routes
- Reusable service functions
- External API integrations

### Type Hints

All functions across the codebase include comprehensive type hints:

- Function parameters with types
- Return type annotations
- Optional and Union types where applicable
- Import types from `typing` module

## Testing Strategy

### Unit Tests

- Test individual functions
- Mock external dependencies
- Focus on business logic

### Integration Tests

- Test API endpoints end-to-end
- Mock Redis only
- Test request/response flow

### Fixtures (conftest.py)

- `client`: Async HTTP client
- `mock_redis`: Mocked Redis client
- `sample_pdf_content`: Test PDF data
- `task_id`: Sample task ID
- Status fixtures for different states

## Development Workflow

### 1. Make Changes

Edit files in `app/` directory:

- Add endpoints in `app/routes/api.py`
- Add models in `app/models/schemas.py`
- Add services in `app/services/`

### 2. Write Tests

Add tests in `tests/`:

```python
@pytest.mark.asyncio
async def test_my_feature(client):
    response = await client.get("/my-endpoint")
    assert response.status_code == 200
```

### 3. Run Tests

```bash
pytest --cov=app
```

### 4. Check Coverage

Ensure >80% coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

### 5. Run Linting (Optional)

```bash
# Install linting tools
pip install ruff black mypy

# Run formatters
black app/ tests/
ruff check app/ tests/

# Type checking
mypy app/
```

## Common Development Tasks

### Add New Endpoint

1. Define Pydantic model in `app/models/schemas.py`
2. Add route in `app/routes/api.py`
3. Add service logic if needed
4. Write tests in `tests/test_api.py`

### Add New Configuration

1. Add to `.env` file
2. Add to `app/config.py` Settings class
3. Use via `from app.config import settings`

### Debug Issues

```bash
# Run with debugging
python -m pdb -m app.main

# Add breakpoint in code
import pdb; pdb.set_trace()

# Check logs
# Logs are printed to console by default
```

## API Development

### Test API Locally

```bash
# Using curl
curl -X POST "http://localhost:8000/upload" \
  -F "files=@test.pdf" \
  -F "mode=pypdf"

# Using HTTPie (if installed)
http POST localhost:8000/upload \
  files@test.pdf \
  mode=pypdf

# Using Python requests
python -c "
import requests
with open('test.pdf', 'rb') as f:
    r = requests.post('http://localhost:8000/upload',
                      files={'files': f},
                      data={'mode': 'pypdf'})
    print(r.json())
"
```

### Interactive API Docs

Open in browser:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Debugging Tips

### Check Redis

```bash
# Connect to Redis CLI
redis-cli

# Check stream
XINFO STREAM pdf_processing_tasks

# Check consumer group
XINFO GROUPS pdf_processing_tasks

# Check task status
GET "task:<task_id>:status"
```

### Check Worker Logs

```bash
# Run worker with verbose logging
PYTHONUNBUFFERED=1 python worker.py

# Check if worker is processing
ps aux | grep worker.py
```

### Check API Logs

```bash
# API logs show in terminal where uvicorn is running
# Look for:
# - Request logs
# - Error tracebacks
# - Info messages
```

## Logging

### Logging Configuration

The application uses a comprehensive logging setup with:

- **Console output** (stdout) for development
- **File logging** in `logs/` directory
- **Request/Response logging** via middleware
- **Structured format** with timestamps

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause application failure

### Log Files

Logs are stored in: `logs/app_YYYYMMDD.log`

Example: `logs/app_20260112.log`

### Viewing Logs

```bash
# View real-time logs
tail -f logs/app_*.log

# Search for errors
grep ERROR logs/app_*.log

# Search for specific task
grep "task_id: abc-123" logs/app_*.log

# View last 100 lines
tail -n 100 logs/app_*.log
```

### What Gets Logged

**Requests:**

- HTTP method and path
- Client IP address
- Request duration
- Status code

**Operations:**

- File uploads (size, count)
- Task creation (task_id)
- Status checks
- Downloads
- Errors and exceptions

**Example Log Output:**

```
2026-01-12 10:30:15 - app.routes.api - INFO - Upload request received: 2 files, mode=pypdf
2026-01-12 10:30:15 - app.routes.api - INFO - Generated task_id: 550e8400-e29b-41d4-a716-446655440000
2026-01-12 10:30:15 - app.routes.api - INFO - Total upload size: 2048576 bytes (2.00 MB)
2026-01-12 10:30:15 - app.middleware - INFO - [12345] POST /upload - Status: 200 - Duration: 0.123s
```

### Middleware Logging

Two middleware components:

1. **LoggingMiddleware** - Logs all requests/responses
2. **ErrorLoggingMiddleware** - Catches and logs unhandled exceptions

Each request gets:

- Unique request ID
- Timing information
- Custom headers (`X-Request-ID`, `X-Process-Time`)

### Adjust Log Levels

Edit `app/logging_config.py`:

```python
# Change main log level
logging.basicConfig(level=logging.DEBUG)  # More verbose

# Adjust specific loggers
logging.getLogger("redis").setLevel(logging.ERROR)  # Less Redis noise
logging.getLogger("uvicorn").setLevel(logging.WARNING)
```

### Disable File Logging

In `app/logging_config.py`, remove the `FileHandler`:

```python
handlers=[
    logging.StreamHandler(sys.stdout),
    # Comment out file handler
    # logging.FileHandler(...)
]
```

## Performance Testing

### Load Testing (Optional)

```bash
# Install locust
pip install locust

# Create locustfile.py and run
locust -f locustfile.py
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests Failing

1. Check Redis is running: `redis-cli ping`
2. Check dependencies: `pip install -e ".[dev]"`
3. Run with verbose: `pytest -v -s`
4. Check fixtures in `conftest.py`

### Import Errors

```bash
# Ensure app is installed in editable mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### Coverage Too Low

1. Run: `pytest --cov=app --cov-report=term-missing`
2. Check which lines are missing
3. Add tests for uncovered code
4. Focus on critical paths first

## Best Practices

### Backend

1. **Write tests first** (TDD)
2. **Keep functions small** (<50 lines)
3. **Use type hints** everywhere
4. **Document with docstrings**
5. **Mock external services** in tests
6. **Keep routes thin** (logic in services)
7. **Use Pydantic** for validation
8. **Log important events**
9. **Handle errors gracefully**
10. **Test edge cases**

### Frontend

1. **Component-based architecture** - Keep components small and focused
2. **Props validation** - Use PropTypes or TypeScript
3. **Error boundaries** - Catch and handle errors gracefully
4. **Loading states** - Always show feedback during async operations
5. **Responsive design** - Test on multiple screen sizes
6. **Accessibility** - Use semantic HTML and ARIA labels
7. **Performance** - Optimize re-renders with React.memo when needed
8. **Clean code** - Follow React naming conventions
9. **State management** - Keep state as local as possible
10. **API integration** - Handle errors and loading states properly

### Full Stack

1. **API contracts** - Keep frontend and backend in sync
2. **CORS configuration** - Properly configure allowed origins
3. **Error handling** - Consistent error format across stack
4. **Documentation** - Keep README files up to date
5. **Version control** - Use meaningful commit messages
6. **Security** - Never commit secrets or API keys
7. **Testing** - Test both frontend and backend independently
8. **Deployment** - Have separate deployment strategies
9. **Monitoring** - Log errors and track performance
10. **Code reviews** - Review changes before merging
