import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { evaluationApi } from '../services/api';

interface DashboardStats {
  averageRating: number;
  totalInteractions: number;
  helpfulPercentage: number;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const metrics = await evaluationApi.getMetrics();
        if (metrics.data) {
          setStats({
            averageRating: metrics.data.average_rating || 0,
            totalInteractions: metrics.data.total_interactions || 0,
            helpfulPercentage: metrics.data.helpful_percentage || 0
          });
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
        // Set default values on error
        setStats({ averageRating: 0, totalInteractions: 0, helpfulPercentage: 0 });
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h1>Dr. Ikechukwu PA</h1>
        <p>Your Multimodal AI Personal Assistant</p>
      </header>

      <main className="dashboard-main">
        <section className="stats-section">
          <div className="stat-card">
            <h3>Total Interactions</h3>
            <p className="stat-value">{isLoading ? '...' : stats?.totalInteractions || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Average Rating</h3>
            <p className="stat-value">{isLoading ? '...' : stats?.averageRating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card">
            <h3>Helpful Rate</h3>
            <p className="stat-value">{isLoading ? '...' : `${stats?.helpfulPercentage || 0}%`}</p>
          </div>
        </section>

        <section className="domains-section">
          <h2>Choose a Domain</h2>
          <div className="domain-cards">
            <Link to="/clinical" className="domain-card clinical">
              <div className="domain-icon">🩺</div>
              <h3>Clinical Decision Support</h3>
              <p>AI-powered medical assistance</p>
            </Link>

            <Link to="/finance" className="domain-card finance">
              <div className="domain-icon">💰</div>
              <h3>Wealth Management</h3>
              <p>Financial analysis & planning</p>
            </Link>

            <Link to="/ai-dev" className="domain-card ai-dev">
              <div className="domain-icon">🤖</div>
              <h3>AI Development Lab</h3>
              <p>Code analysis & debugging</p>
            </Link>

            <Link to="/fashion" className="domain-card fashion">
              <div className="domain-icon">👔</div>
              <h3>Fashion & Lifestyle</h3>
              <p>Style recommendations</p>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
