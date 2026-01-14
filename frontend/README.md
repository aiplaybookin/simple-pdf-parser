# Intelligent Document Processing - Frontend

Professional React frontend for the Intelligent Document Processing API.

## Features

- 📤 **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- 🔄 **Real-time Progress**: Live progress tracking with visual feedback
- 🤖 **Dual Processing Modes**: Choose between PyPDF (fast) or Gemini AI (advanced)
- 📊 **AI Summaries**: View AI-generated summaries for each document
- ⬇️ **Easy Downloads**: Download processed markdown files individually or as a ZIP
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at **http://localhost:5173**

## Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000
- Redis running on localhost:6379
- Worker process running (python worker.py)

## Usage

1. **Upload Documents**: Drag & drop PDF files or click to browse
2. **Select Mode**: Choose PyPDF (fast) or Gemini AI (advanced OCR)
3. **Monitor Progress**: View real-time progress with file-by-file tracking
4. **View Results**: Expand to see AI-generated summaries
5. **Download**: Get all files as ZIP or individual markdown files

## API Configuration

Backend API URL is set to `http://localhost:8000`. To change:

Update `API_BASE_URL` in:
- `src/App.jsx`
- `src/components/Processing.jsx`
- `src/components/Results.jsx`

## Building for Production

```bash
npm run build
npm run preview
```

## Troubleshooting

**CORS Errors**: Ensure backend CORS middleware allows http://localhost:5173

**API Connection**: Verify backend is running: `curl http://localhost:8000/health`

**Build Issues**: Clear cache with `rm -rf node_modules && npm install`
