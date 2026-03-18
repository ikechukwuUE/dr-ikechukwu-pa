import React, { useState } from 'react';
import { submitFeedback, getErrorMessage } from '../services/api';

interface RatingDialogProps {
  interactionId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

export const RatingDialog: React.FC<RatingDialogProps> = ({
  interactionId,
  isOpen,
  onClose,
  onSubmitSuccess
}) => {
  const [rating, setRating] = useState<number>(0);
  const [helpful, setHelpful] = useState<boolean | null>(null);
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (rating === 0) {
      setError('Please provide a rating');
      return;
    }

    if (helpful === null) {
      setError('Please indicate if the response was helpful');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await submitFeedback({
        interactionId,
        rating,
        helpful,
        feedback: feedback.trim() || undefined
      });

      // Reset form
      setRating(0);
      setHelpful(null);
      setFeedback('');
      
      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <button
          key={i}
          type="button"
          className={`star-button ${i <= rating ? 'active' : ''}`}
          onClick={() => setRating(i)}
          disabled={isSubmitting}
        >
          {i <= rating ? '★' : '☆'}
        </button>
      );
    }
    return stars;
  };

  return (
    <div className="rating-dialog-overlay">
      <div className="rating-dialog">
        <div className="rating-dialog-header">
          <h3>Rate Your Experience</h3>
          <button 
            type="button" 
            className="close-button"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="rating-form-group">
            <label>How would you rate this response?</label>
            <div className="star-rating">
              {renderStars()}
            </div>
            <span className="rating-label">
              {rating === 0 ? 'Tap to rate' :
               rating === 1 ? 'Poor' :
               rating === 2 ? 'Fair' :
               rating === 3 ? 'Good' :
               rating === 4 ? 'Very Good' :
               'Excellent'}
            </span>
          </div>

          <div className="rating-form-group">
            <label>Was this response helpful?</label>
            <div className="helpful-buttons">
              <button
                type="button"
                className={`helpful-button ${helpful === true ? 'active' : ''}`}
                onClick={() => setHelpful(true)}
                disabled={isSubmitting}
              >
                👍 Yes
              </button>
              <button
                type="button"
                className={`helpful-button ${helpful === false ? 'active' : ''}`}
                onClick={() => setHelpful(false)}
                disabled={isSubmitting}
              >
                👎 No
              </button>
            </div>
          </div>

          <div className="rating-form-group">
            <label htmlFor="feedback">Additional Feedback (Optional)</label>
            <textarea
              id="feedback"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Tell us more about your experience..."
              disabled={isSubmitting}
              rows={3}
            />
          </div>

          {error && (
            <div className="rating-error">
              {error}
            </div>
          )}

          <div className="rating-dialog-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="submit-button"
              disabled={isSubmitting || rating === 0 || helpful === null}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RatingDialog;
