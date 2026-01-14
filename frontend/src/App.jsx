import { useState } from 'react';
import './App.css';
import Upload from './components/Upload';
import Processing from './components/Processing';
import Results from './components/Results';
import ErrorDisplay from './components/ErrorDisplay';
import { API_BASE_URL } from './config';

function App() {
  const [view, setView] = useState('upload'); // upload, processing, results, error
  const [taskId, setTaskId] = useState(null);
  const [files, setFiles] = useState([]);
  const [mode, setMode] = useState('pypdf');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (selectedFiles, selectedMode) => {
    setFiles(selectedFiles);
    setMode(selectedMode);
    setView('processing');

    try {
      // Upload files
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('mode', selectedMode);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setTaskId(data.task_id);
    } catch (err) {
      setError(err.message);
      setView('error');
    }
  };

  const handleProcessingComplete = (resultsData) => {
    setResults(resultsData);
    setView('results');
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setView('error');
  };

  const handleReset = () => {
    setView('upload');
    setTaskId(null);
    setFiles([]);
    setMode('pypdf');
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <path d="M20 4L4 12V28L20 36L36 28V12L20 4Z" stroke="#667eea" strokeWidth="2" fill="none"/>
            <circle cx="20" cy="20" r="6" fill="#667eea"/>
          </svg>
          <div>
            <h1>Intelligent Document Processing</h1>
            <p className="subtitle">AI-Powered PDF Analysis & Summarization</p>
          </div>
        </div>
      </header>

      <main className="main-content">
        {view === 'upload' && <Upload onUpload={handleUpload} />}
        {view === 'processing' && (
          <Processing
            taskId={taskId}
            files={files}
            mode={mode}
            onComplete={handleProcessingComplete}
            onError={handleError}
          />
        )}
        {view === 'results' && (
          <Results
            results={results}
            taskId={taskId}
            onReset={handleReset}
          />
        )}
        {view === 'error' && (
          <ErrorDisplay
            error={error}
            onRetry={handleReset}
          />
        )}
      </main>
    </div>
  );
}

export default App;
