import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ChatInterface from '../components/ChatInterface';
import RatingDialog from '../components/RatingDialog';
import { 
  getPendingApprovals, 
  approveFinanceAction, 
  rejectFinanceAction,
  getErrorMessage 
} from '../services/api';

interface PendingApproval {
  id: string;
  type: string;
  amount?: number;
  description: string;
  timestamp: string;
}

export const Finance: React.FC = () => {
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRating, setShowRating] = useState(false);
  const [lastInteractionId, setLastInteractionId] = useState<string>('');
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const fetchPendingApprovals = async () => {
    try {
      const approvals = await getPendingApprovals();
      setPendingApprovals(approvals);
    } catch (error) {
      console.error('Error fetching approvals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (actionId: string) => {
    setProcessingId(actionId);
    try {
      await approveFinanceAction(actionId);
      setPendingApprovals(prev => prev.filter(a => a.id !== actionId));
    } catch (error) {
      console.error('Error approving:', error);
      alert('Failed to approve: ' + getErrorMessage(error));
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (actionId: string) => {
    const reason = prompt('Please provide a reason for rejection:');
    if (!reason) return;

    setProcessingId(actionId);
    try {
      await rejectFinanceAction(actionId, reason);
      setPendingApprovals(prev => prev.filter(a => a.id !== actionId));
    } catch (error) {
      console.error('Error rejecting:', error);
      alert('Failed to reject: ' + getErrorMessage(error));
    } finally {
      setProcessingId(null);
    }
  };

  const handleResponse = (response: unknown) => {
    const resp = response as { hitlRequired?: boolean };
    if (resp.hitlRequired) {
      // Refresh pending approvals after HITL request
      setTimeout(fetchPendingApprovals, 1000);
    }
    setLastInteractionId(`finance-${Date.now()}`);
    setTimeout(() => setShowRating(true), 2000);
  };

  return (
    <div className="domain-page finance-page">
      <header className="domain-header">
        <div className="header-nav">
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
        </div>
        <div className="header-content">
          <h1>💰 Financial Analysis</h1>
          <p>Smart financial queries with human-in-the-loop approval</p>
        </div>
      </header>

      <main className="domain-main">
        <div className="content-grid">
          <div className="chat-section">
            <ChatInterface domain="finance" onResponse={handleResponse} />
          </div>

          <aside className="sidebar">
            <div className="pending-approvals-card">
              <h3>Pending Approvals</h3>
              
              {isLoading ? (
                <div className="loading-small">
                  <div className="spinner-small"></div>
                </div>
              ) : pendingApprovals.length === 0 ? (
                <p className="no-approvals">No pending approvals</p>
              ) : (
                <ul className="approvals-list">
                  {pendingApprovals.map((approval) => (
                    <li key={approval.id} className="approval-item">
                      <div className="approval-info">
                        <span className="approval-type">{approval.type}</span>
                        {approval.amount && (
                          <span className="approval-amount">
                            ${approval.amount.toLocaleString()}
                          </span>
                        )}
                        <span className="approval-description">
                          {approval.description}
                        </span>
                        <span className="approval-time">
                          {new Date(approval.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="approval-actions">
                        <button
                          className="approve-btn"
                          onClick={() => handleApprove(approval.id)}
                          disabled={processingId === approval.id}
                        >
                          ✓ Approve
                        </button>
                        <button
                          className="reject-btn"
                          onClick={() => handleReject(approval.id)}
                          disabled={processingId === approval.id}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="reflection-status-card">
              <h3>Reflection Status</h3>
              <div className="status-indicator">
                <span className="status-dot active"></span>
                <span>Reflection Agent Active</span>
              </div>
              <p className="reflection-description">
                Financial transactions over $10,000 require reflection review 
                before execution.
              </p>
            </div>

            <div className="info-card">
              <h3>Features</h3>
              <ul className="feature-list">
                <li>Transaction analysis</li>
                <li>Fraud detection</li>
                <li>Investment recommendations</li>
                <li>Budget optimization</li>
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

export default Finance;
