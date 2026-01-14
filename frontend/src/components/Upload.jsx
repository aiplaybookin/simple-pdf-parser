import { useState, useRef } from 'react';
import './Upload.css';

function Upload({ onUpload }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [mode, setMode] = useState('pypdf');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (files) => {
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    setSelectedFiles(prev => [...prev, ...pdfFiles]);
  };

  const handleFileInputChange = (e) => {
    handleFileSelect(e.target.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handleSubmit = () => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles, mode);
    }
  };

  return (
    <div className="upload-container">
      <div className="card">
        <h2>Upload Documents</h2>
        <p className="description">Select PDF files for processing and AI summarization</p>

        <div
          className={`upload-area ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <div className="upload-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <path d="M32 8V40M32 40L20 28M32 40L44 28" stroke="#667eea" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M52 40V52C52 53.1046 51.1046 54 50 54H14C12.8954 54 12 53.1046 12 52V40" stroke="#667eea" strokeWidth="3" strokeLinecap="round"/>
            </svg>
          </div>
          <h3>Drag & Drop PDF Files</h3>
          <p>or click to browse</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>

        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <h3>Selected Files ({selectedFiles.length})</h3>
            <div className="files-list">
              {selectedFiles.map((file, index) => (
                <div key={index} className="file-item">
                  <div className="file-icon">📄</div>
                  <div className="file-info">
                    <div className="file-name">{file.name}</div>
                    <div className="file-size">{formatFileSize(file.size)}</div>
                  </div>
                  <button
                    className="remove-btn"
                    onClick={() => removeFile(index)}
                    aria-label="Remove file"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mode-selection">
          <label className="mode-label">Processing Mode:</label>
          <div className="radio-group">
            <label className={`radio-option ${mode === 'pypdf' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="mode"
                value="pypdf"
                checked={mode === 'pypdf'}
                onChange={(e) => setMode(e.target.value)}
              />
              <span className="radio-custom"></span>
              <div className="radio-content">
                <strong>PyPDF</strong>
                <small>Fast text extraction</small>
              </div>
            </label>
            <label className={`radio-option ${mode === 'gemini' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="mode"
                value="gemini"
                checked={mode === 'gemini'}
                onChange={(e) => setMode(e.target.value)}
              />
              <span className="radio-custom"></span>
              <div className="radio-content">
                <strong>Gemini AI</strong>
                <small>Advanced OCR & analysis</small>
              </div>
            </label>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={selectedFiles.length === 0}
        >
          <span>Process {selectedFiles.length} Document{selectedFiles.length !== 1 ? 's' : ''}</span>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3L17 10L10 17M17 10H3" stroke="currentColor" strokeWidth="2" fill="none"/>
          </svg>
        </button>
      </div>
    </div>
  );
}

export default Upload;
