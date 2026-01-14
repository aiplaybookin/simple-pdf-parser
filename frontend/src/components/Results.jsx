import { useState } from 'react';
import './Results.css';
import { API_BASE_URL } from '../config';

function Results({ results, taskId, onReset }) {
  const [expandedFiles, setExpandedFiles] = useState(new Set());

  const toggleExpand = (filename) => {
    setExpandedFiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(filename)) {
        newSet.delete(filename);
      } else {
        newSet.add(filename);
      }
      return newSet;
    });
  };

  const handleDownloadAll = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/download-markdown/${taskId}`);
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Check if it's a zip file or markdown
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('zip')) {
        a.download = `documents_${taskId}.zip`;
      } else {
        a.download = `document_${taskId}.md`;
      }

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download files. Please try again.');
    }
  };

  const fileCount = results?.summaries ? Object.keys(results.summaries).length : 0;

  return (
    <div className="results-container">
      <div className="card">
        <div className="results-header">
          <div className="success-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="22" fill="#10b981" opacity="0.1"/>
              <path d="M14 24L20 30L34 16" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h2>Processing Complete!</h2>
            <p className="results-info">
              Successfully processed {fileCount} document{fileCount !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        <div className="results-list">
          {results?.summaries && Object.entries(results.summaries).map(([filename, summary]) => {
            const isExpanded = expandedFiles.has(filename);
            return (
              <div key={filename} className="result-item">
                <div className="result-header" onClick={() => toggleExpand(filename)}>
                  <div className="file-icon">📄</div>
                  <div className="result-content">
                    <h3>{filename}</h3>
                    <p className="file-meta">
                      {summary.length} characters
                    </p>
                  </div>
                  <button className="expand-button">
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      style={{
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s ease'
                      }}
                    >
                      <path
                        d="M6 9L12 15L18 9"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>

                {isExpanded && (
                  <div className="result-summary">
                    <h4>Summary</h4>
                    <div className="summary-content">
                      {summary}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="results-actions">
          <button className="btn-primary" onClick={handleDownloadAll}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 3V13M10 13L6 9M10 13L14 9" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 15V16C3 16.5523 3.44772 17 4 17H16C16.5523 17 17 16.5523 17 16V15" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
            </svg>
            <span>Download All Markdown Files</span>
          </button>
          <button className="btn-outline" onClick={onReset}>
            <span>Process More Documents</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Results;
