import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ChatInterface from '../components/ChatInterface';
import RatingDialog from '../components/RatingDialog';

export const Clinical: React.FC = () => {
  const [showRating, setShowRating] = useState(false);
  const [lastInteractionId, setLastInteractionId] = useState<string>('');

  const handleResponse = (response: unknown) => {
    // Generate interaction ID from response
    const resp = response as { response?: string };
    if (resp.response) {
      setLastInteractionId(`cds-${Date.now()}`);
      // Show rating dialog after response
      setTimeout(() => setShowRating(true), 2000);
    }
  };

  const agentStatus = [
    { name: 'Triage Agent', status: 'active', icon: '🎯' },
    { name: 'Drug Interaction Agent', status: 'active', icon: '💊' },
    { name: 'Diagnostic Agent', status: 'active', icon: '🔬' },
    { name: 'Treatment Agent', status: 'ready', icon: '🩹' }
  ];

  return (
    <div className="domain-page clinical-page">
      <header className="domain-header">
        <div className="header-nav">
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
        </div>
        <div className="header-content">
          <h1>🩺 Clinical Decision Support</h1>
          <p>AI-powered clinical assistance for healthcare professionals</p>
        </div>
      </header>

      <main className="domain-main">
        <div className="content-grid">
          <div className="chat-section">
            <ChatInterface domain="cds" onResponse={handleResponse} />
          </div>

          <aside className="sidebar">
            <div className="agent-status-card">
              <h3>Agent Status</h3>
              <ul className="agent-list">
                {agentStatus.map((agent) => (
                  <li key={agent.name} className="agent-item">
                    <span className="agent-icon">{agent.icon}</span>
                    <span className="agent-name">{agent.name}</span>
                    <span className={`agent-status-badge ${agent.status}`}>
                      {agent.status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="info-card">
              <h3>Quick Actions</h3>
              <ul className="quick-actions">
                <li>
                  <button className="quick-action-btn">
                    Check Drug Interactions
                  </button>
                </li>
                <li>
                  <button className="quick-action-btn">
                    Get Diagnostic Suggestions
                  </button>
                </li>
                <li>
                  <button className="quick-action-btn">
                    View Patient History
                  </button>
                </li>
              </ul>
            </div>

            <div className="disclaimer-card">
              <h3>⚠️ Disclaimer</h3>
              <p>
                This AI assistant provides suggestions only. Always consult 
                with qualified healthcare professionals for final decisions.
              </p>
            </div>
          </aside>
        </div>
      </main>

      <RatingDialog
        interactionId={lastInteractionId}
        isOpen={showRating}
        onClose={() => setShowRating(false)}
        onSubmitSuccess={() => {
          console.log('Feedback submitted successfully');
        }}
      />
    </div>
  );
};

export default Clinical;
