import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { analyzeCode, getErrorMessage, type AIDevResponse } from '../services/api';
import { useAuth0 } from '@auth0/auth0-react';
import RatingDialog from '../components/RatingDialog';

type AnalysisType = 'security' | 'performance' | 'best_practices' | 'full';

export const AIDev: React.FC = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [code, setCode] = useState('');
  const [analysisType, setAnalysisType] = useState<AnalysisType>('full');
  const [language, setLanguage] = useState('python');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<AIDevResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRating, setShowRating] = useState(false);
  const [lastInteractionId, setLastInteractionId] = useState<string>('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || isAnalyzing) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);

    try {
      const response = await analyzeCode({
        code: code,
        language,
        analysisType
      });
      setResults(response);
      setLastInteractionId(`aidev-${Date.now()}`);
      setTimeout(() => setShowRating(true), 2000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#ca8a04';
      case 'low': return '#16a34a';
      default: return '#6b7280';
    }
  };

  return (
    <div className="domain-page aidev-page">
      <header className="domain-header">
        <div className="header-nav">
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
        </div>
        <div className="header-content">
          <h1>👨‍💻 AI Development Tools</h1>
          <p>Code analysis for security, performance, and best practices</p>
        </div>
      </header>

      <main className="domain-main">
        <div className="content-grid">
          <div className="code-section">
            <form onSubmit={handleAnalyze} className="code-form">
              <div className="code-options">
                <div className="option-group">
                  <label htmlFor="language">Language:</label>
                  <select
                    id="language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={isAnalyzing}
                  >
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="csharp">C#</option>
                    <option value="go">Go</option>
                    <option value="rust">Rust</option>
                  </select>
                </div>

                <div className="option-group">
                  <label htmlFor="analysisType">Analysis Type:</label>
                  <select
                    id="analysisType"
                    value={analysisType}
                    onChange={(e) => setAnalysisType(e.target.value as AnalysisType)}
                    disabled={isAnalyzing}
                  >
                    <option value="full">Full Analysis</option>
                    <option value="security">Security Only</option>
                    <option value="performance">Performance Only</option>
                    <option value="best_practices">Best Practices Only</option>
                  </select>
                </div>

                <button 
                  type="submit" 
                  className="analyze-button"
                  disabled={isAnalyzing || !code.trim()}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Code'}
                </button>
              </div>

              <div className="code-input-container">
                <label htmlFor="code">Paste your code:</label>
                <textarea
                  id="code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="// Paste your code here..."
                  disabled={isAnalyzing}
                  rows={15}
                  className="code-input"
                />
              </div>
            </form>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {results && (
              <div className="analysis-results">
                <h3>Analysis Results</h3>
                
                <div className="analysis-summary">
                  <div className="summary-content">
                    <p>{results.analysis}</p>
                  </div>
                </div>

                {results.issues.length > 0 && (
                  <div className="issues-section">
                    <h4>Issues Found ({results.issues.length})</h4>
                    <ul className="issues-list">
                      {results.issues.map((issue, index) => (
                        <li 
                          key={index} 
                          className="issue-item"
                          style={{ borderLeftColor: getSeverityColor(issue.severity) }}
                        >
                          <div className="issue-header">
                            <span 
                              className="issue-severity"
                              style={{ backgroundColor: getSeverityColor(issue.severity) }}
                            >
                              {issue.severity}
                            </span>
                            {issue.line && (
                              <span className="issue-line">Line {issue.line}</span>
                            )}
                          </div>
                          <p className="issue-message">{issue.message}</p>
                          {issue.suggestion && (
                            <p className="issue-suggestion">
                              <strong>Suggestion:</strong> {issue.suggestion}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {results.suggestions.length > 0 && (
                  <div className="suggestions-section">
                    <h4>Suggestions</h4>
                    <ul className="suggestions-list">
                      {results.suggestions.map((suggestion, index) => (
                        <li key={index}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          <aside className="sidebar">
            <div className="info-card">
              <h3>Supported Languages</h3>
              <ul className="language-list">
                <li>Python</li>
                <li>JavaScript</li>
                <li>TypeScript</li>
                <li>Java</li>
                <li>C#</li>
                <li>Go</li>
                <li>Rust</li>
              </ul>
            </div>

            <div className="info-card">
              <h3>Analysis Types</h3>
              <ul className="analysis-types">
                <li><strong>Security:</strong> Find vulnerabilities</li>
                <li><strong>Performance:</strong> Optimization opportunities</li>
                <li><strong>Best Practices:</strong> Code quality</li>
                <li><strong>Full:</strong> All of the above</li>
              </ul>
            </div>
          </aside>
        </div>
      </main>

      <RatingDialog
        interactionId={lastInteractionId}
        isOpen={showRating}
        onClose={() => setShowRating(false)}
      />
    </div>
  );
};

export default AIDev;
