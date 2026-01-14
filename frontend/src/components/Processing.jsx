import { useState, useEffect } from 'react';
import './Processing.css';
import { API_BASE_URL } from '../config';

function Processing({ taskId, files, mode, onComplete, onError }) {
  const [status, setStatus] = useState('PENDING');
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState(0);
  const [message, setMessage] = useState('Initializing...');
  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    if (!taskId) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/status/${taskId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }

        const data = await response.json();
        setStatus(data.state || data.status);
        setMessage(data.message || '');

        if (data.current !== undefined && data.total !== undefined) {
          setCurrentFile(data.current);
          const percentComplete = Math.round((data.current / data.total) * 100);
          setProgress(percentComplete);

          // Update active step based on progress
          if (percentComplete === 0) {
            setActiveStep(1);
          } else if (percentComplete < 50) {
            setActiveStep(2);
          } else if (percentComplete < 100) {
            setActiveStep(3);
          } else {
            setActiveStep(4);
          }
        }

        if (data.state === 'SUCCESS' || data.status === 'SUCCESS') {
          setProgress(100);
          setActiveStep(4);
          // Fetch results
          try {
            const resultsResponse = await fetch(`${API_BASE_URL}/download/${taskId}`);
            if (!resultsResponse.ok) {
              throw new Error('Failed to fetch results');
            }
            const resultsData = await resultsResponse.json();
            setTimeout(() => onComplete(resultsData), 1000);
          } catch (err) {
            onError(err.message);
          }
        } else if (data.state === 'FAILURE' || data.status === 'FAILURE') {
          onError(data.error || 'Processing failed');
        }
      } catch (err) {
        onError(err.message);
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [taskId, onComplete, onError]);

  return (
    <div className="processing-container">
      <div className="card">
        <div className="processing-header">
          <div className="spinner"></div>
          <div>
            <h2>Processing Documents</h2>
            <p className="processing-status">{message}</p>
            <p className="processing-mode">Mode: {mode === 'pypdf' ? 'PyPDF' : 'Gemini AI'}</p>
          </div>
        </div>

        <div className="progress-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-info">
            <span className="progress-text">{progress}%</span>
            <span className="progress-files">
              {currentFile} / {files.length} files
            </span>
          </div>
        </div>

        <div className="processing-steps">
          <div className={`step ${activeStep >= 1 ? 'active' : ''} ${activeStep > 1 ? 'complete' : ''}`}>
            <div className="step-icon">
              {activeStep > 1 ? '✓' : '1'}
            </div>
            <span>Uploading</span>
          </div>
          <div className={`step ${activeStep >= 2 ? 'active' : ''} ${activeStep > 2 ? 'complete' : ''}`}>
            <div className="step-icon">
              {activeStep > 2 ? '✓' : '2'}
            </div>
            <span>Extracting</span>
          </div>
          <div className={`step ${activeStep >= 3 ? 'active' : ''} ${activeStep > 3 ? 'complete' : ''}`}>
            <div className="step-icon">
              {activeStep > 3 ? '✓' : '3'}
            </div>
            <span>Summarizing</span>
          </div>
          <div className={`step ${activeStep >= 4 ? 'active' : ''} ${activeStep > 4 ? 'complete' : ''}`}>
            <div className="step-icon">
              {activeStep > 4 ? '✓' : '4'}
            </div>
            <span>Complete</span>
          </div>
        </div>

        <div className="files-processing">
          <h3>Files in Queue</h3>
          <div className="files-list">
            {files.map((file, index) => (
              <div
                key={index}
                className={`file-item ${index < currentFile ? 'complete' : ''} ${index === currentFile ? 'current' : ''}`}
              >
                <div className="file-icon">
                  {index < currentFile ? '✓' : '📄'}
                </div>
                <div className="file-info">
                  <div className="file-name">{file.name}</div>
                  {index === currentFile && (
                    <div className="file-status">Processing...</div>
                  )}
                  {index < currentFile && (
                    <div className="file-status complete">Complete</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Processing;
