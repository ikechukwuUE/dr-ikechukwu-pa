import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { getFashionRecommendations, getErrorMessage, type FashionResponse } from '../services/api';
import RatingDialog from '../components/RatingDialog';

export const Fashion: React.FC = () => {
  const [style, setStyle] = useState('');
  const [preferences, setPreferences] = useState('');
  const [occasion, setOccasion] = useState('casual');
  const [bodyType, setBodyType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<FashionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRating, setShowRating] = useState(false);
  const [lastInteractionId, setLastInteractionId] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!style.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await getFashionRecommendations({
        style: style,
        preferences: preferences.trim() || undefined,
        occasion,
        bodyType: bodyType.trim() || undefined
      });
      setResults(response);
      setLastInteractionId(`fashion-${Date.now()}`);
      setTimeout(() => setShowRating(true), 2000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const occasions = [
    { value: 'casual', label: 'Casual Everyday' },
    { value: 'business', label: 'Business/Professional' },
    { value: 'formal', label: 'Formal Event' },
    { value: 'party', label: 'Party/Celebration' },
    { value: 'date', label: 'Date Night' },
    { value: 'workout', label: 'Workout/Sports' },
    { value: 'vacation', label: 'Vacation' }
  ];

  return (
    <div className="domain-page fashion-page">
      <header className="domain-header">
        <div className="header-nav">
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
        </div>
        <div className="header-content">
          <h1>👗 Fashion Styling</h1>
          <p>Personalized style recommendations based on your preferences</p>
        </div>
      </header>

      <main className="domain-main">
        <div className="content-grid">
          <div className="fashion-section">
            <form onSubmit={handleSubmit} className="fashion-form">
              <div className="form-group">
                <label htmlFor="style">Your Style *</label>
                <input
                  id="style"
                  type="text"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  placeholder="e.g., modern, classic, bohemian, streetwear..."
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="occasion">Occasion</label>
                  <select
                    id="occasion"
                    value={occasion}
                    onChange={(e) => setOccasion(e.target.value)}
                    disabled={isLoading}
                  >
                    {occasions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="bodyType">Body Type (Optional)</label>
                  <input
                    id="bodyType"
                    type="text"
                    value={bodyType}
                    onChange={(e) => setBodyType(e.target.value)}
                    placeholder="e.g., athletic, petite, tall..."
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="preferences">Additional Preferences</label>
                <textarea
                  id="preferences"
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  placeholder="Colors you like, fabrics, budget..."
                  disabled={isLoading}
                  rows={3}
                />
              </div>

              <button 
                type="submit" 
                className="submit-button"
                disabled={isLoading || !style.trim()}
              >
                {isLoading ? 'Getting Recommendations...' : 'Get Recommendations'}
              </button>
            </form>

            {/* Image Upload Placeholder */}
            <div className="upload-section">
              <div className="upload-placeholder">
                <span className="upload-icon">📷</span>
                <p>Upload a photo for personalized recommendations</p>
                <span className="upload-note">(Coming soon)</span>
              </div>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {results && (
              <div className="fashion-results">
                <h3>Your Personalized Recommendations</h3>

                {results.recommendations.length > 0 && (
                  <div className="recommendations-section">
                    <h4>Outfit Recommendations</h4>
                    <ul className="recommendations-list">
                      {results.recommendations.map((rec, index) => (
                        <li key={index} className="recommendation-item">
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {results.stylingTips.length > 0 && (
                  <div className="tips-section">
                    <h4>Styling Tips</h4>
                    <ul className="tips-list">
                      {results.stylingTips.map((tip, index) => (
                        <li key={index}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {results.colorPalette && results.colorPalette.length > 0 && (
                  <div className="color-section">
                    <h4>Recommended Color Palette</h4>
                    <div className="color-palette">
                      {results.colorPalette.map((color, index) => (
                        <div 
                          key={index} 
                          className="color-swatch"
                          style={{ backgroundColor: color }}
                          title={color}
                        >
                          <span className="color-name">{color}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <aside className="sidebar">
            <div className="style-guides-card">
              <h3>Style Guides</h3>
              <ul className="style-list">
                <li>
                  <strong>Modern:</strong> Clean lines, minimal details
                </li>
                <li>
                  <strong>Classic:</strong> Timeless pieces, neutral colors
                </li>
                <li>
                  <strong>Bohemian:</strong> Flowy fabrics, earthy tones
                </li>
                <li>
                  <strong>Streetwear:</strong> Urban, casual, trendy
                </li>
                <li>
                  <strong>Minimalist:</strong> Simple, functional, elegant
                </li>
              </ul>
            </div>

            <div className="trending-card">
              <h3>Trending Now</h3>
              <ul className="trending-list">
                <li>Sustainable fashion</li>
                <li>Mix and match patterns</li>
                <li>Oversized silhouettes</li>
                <li>Bold accessories</li>
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

export default Fashion;
