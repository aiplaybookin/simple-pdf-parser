import './ErrorDisplay.css';

function ErrorDisplay({ error, onRetry }) {
  return (
    <div className="error-container">
      <div className="card error-card">
        <div className="error-icon">⚠️</div>
        <h2>Processing Error</h2>
        <p className="error-message">{error || 'An unexpected error occurred'}</p>
        <button className="btn-outline" onClick={onRetry}>
          <span>Try Again</span>
        </button>
      </div>
    </div>
  );
}

export default ErrorDisplay;
