import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { sendCDSMessage, sendFinanceQuery, getErrorMessage, type Message } from '../services/api';

interface ChatInterfaceProps {
  domain: 'cds' | 'finance' | 'ai-dev' | 'fashion';
  onResponse?: (response: unknown) => void;
}

interface ChatMessage extends Message {
  domain?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ domain, onResponse }) => {
  const { getAccessTokenSilently } = useAuth0();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessages: Record<string, ChatMessage> = {
      'cds': {
        id: 'welcome-cds',
        role: 'assistant',
        content: 'Hello! I\'m your Clinical Decision Support assistant. I can help you with patient care decisions, drug interactions, diagnostic suggestions, and clinical guidelines. How can I assist you today?',
        timestamp: new Date().toISOString(),
        domain: 'cds'
      },
      'finance': {
        id: 'welcome-finance',
        role: 'assistant',
        content: 'Hello! I\'m your Financial Analysis assistant. I can help you with financial queries, transaction analysis, fraud detection, and investment recommendations. What would you like to know?',
        timestamp: new Date().toISOString(),
        domain: 'finance'
      },
      'ai-dev': {
        id: 'welcome-ai-dev',
        role: 'assistant',
        content: 'Hello! I\'m your AI Development assistant. I can help you analyze code for security vulnerabilities, performance issues, and best practices. Paste your code below for analysis.',
        timestamp: new Date().toISOString(),
        domain: 'ai-dev'
      },
      'fashion': {
        id: 'welcome-fashion',
        role: 'assistant',
        content: 'Hello! I\'m your Fashion Styling assistant. I can help you with outfit recommendations, style advice, color matching, and occasion-based dressing. What\'s your style question?',
        timestamp: new Date().toISOString(),
        domain: 'fashion'
      }
    };

    if (messages.length === 0) {
      setMessages([welcomeMessages[domain]]);
    }
  }, [domain, messages.length]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
      domain
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      let response;
      const token = await getAccessTokenSilently();

      switch (domain) {
        case 'cds':
          response = await sendCDSMessage({
            message: userMessage.content,
            context: {}
          });
          break;
        case 'finance':
          response = await sendFinanceQuery({
            query: userMessage.content
          });
          break;
        default:
          response = await sendCDSMessage({
            message: userMessage.content
          });
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response || 'I apologize, but I could not process your request.',
        timestamp: new Date().toISOString(),
        domain
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (onResponse) {
        onResponse(response);
      }
    } catch (err) {
      setError(getErrorMessage(err));
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but an error occurred while processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        domain
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';
    return (
      <div
        key={message.id}
        className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
      >
        <div className="message-content">
          <div className="message-avatar">
            {isUser ? '👤' : '🤖'}
          </div>
          <div className="message-bubble">
            <p>{message.content}</p>
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>
          {domain === 'ai-dev' ? 'AI Development' : 
           domain.charAt(0).toUpperCase() + domain.slice(1)} Assistant
        </h2>
      </div>
      
      <div className="chat-messages">
        {messages.map(renderMessage)}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-content">
              <div className="message-avatar">🤖</div>
              <div className="message-bubble loading">
                <span className="typing-indicator">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Type your ${domain === 'ai-dev' ? 'code or question' : 'message'}...`}
            disabled={isLoading}
            rows={domain === 'ai-dev' ? 6 : 2}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="send-button"
          >
            {isLoading ? '⏳' : '➤'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
