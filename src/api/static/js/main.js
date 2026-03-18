/**
 * DR. IKECHUKWU PA - Global JavaScript
 * Common utilities and initialization for all pages
 */

(function() {
    'use strict';

    // ============================================
    // Global State
    // ============================================
    window.AppState = {
        isLoading: false,
        currentUser: null,
        apiBaseUrl: '',
        theme: 'dark'
    };

    // ============================================
    // Initialization
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
        setupGlobalErrorHandlers();
        initializeWidgets();
    });

    function initializeApp() {
        console.log('DR. IKECHUKWU PA: Initializing application...');
        
        // Set API base URL
        window.AppState.apiBaseUrl = window.location.origin;
        
        // Apply theme
        applyTheme();
        
        // Initialize navigation
        initializeNavigation();
        
        // Setup AJAX defaults
        setupAjaxDefaults();
        
        console.log('DR. IKECHUKWU PA: Application initialized');
    }

    function applyTheme() {
        const html = document.documentElement;
        const theme = html.getAttribute('data-theme') || 'dark';
        window.AppState.theme = theme;
        document.body.classList.add(theme + '-theme');
    }

    function initializeNavigation() {
        // Highlight current nav link
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
            }
        });
    }

    function setupAjaxDefaults() {
        // Setup Axios defaults if available
        if (typeof axios !== 'undefined') {
            axios.defaults.baseURL = window.AppState.apiBaseUrl;
            axios.defaults.timeout = 30000;
            axios.defaults.headers.common['Content-Type'] = 'application/json';
        }
    }

    function setupGlobalErrorHandlers() {
        // Global error handler for uncaught errors
        window.addEventListener('error', function(e) {
            console.error('Global error:', e.error);
        });

        // Handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', function(e) {
            console.error('Unhandled promise rejection:', e.reason);
        });
    }

    // ============================================
    // Widget Initialization
    // ============================================
    function initializeWidgets() {
        console.log('Initializing widgets...');
        
        // Initialize any widget containers
        initializeCards();
        initializeForms();
        initializeButtons();
        
        console.log('Widgets initialized');
    }

    function initializeCards() {
        // Add click handlers to domain cards
        document.querySelectorAll('.domain-card').forEach(card => {
            card.style.cursor = 'pointer';
            
            // Ensure click works even with child elements
            card.addEventListener('click', function(e) {
                if (!e.target.closest('button') && !e.target.closest('a')) {
                    const onclick = this.getAttribute('onclick');
                    if (onclick) {
                        // Allow inline onclick to execute
                    }
                }
            });
        });
    }

    function initializeForms() {
        // Add submit prevention for forms with loading states
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn && submitBtn.disabled) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }

    function initializeButtons() {
        // Add loading state to buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                // Handle any button-specific logic
            });
        });
    }

    // ============================================
    // Utility Functions
    // ============================================
    
    /**
     * Parse Markdown to HTML using marked.js
     */
    window.parseMarkdown = function(text) {
        // Debug: Log the type of text being passed
        console.log('[parseMarkdown] Input type:', typeof text, 'Value:', text);
        
        if (!text) return '';
        if (typeof text !== 'string') {
            console.warn('[parseMarkdown] Non-string input received, converting to string:', text);
            text = String(text);
        }
        if (typeof marked !== 'undefined') {
            // Configure marked for safe rendering
            marked.setOptions({
                breaks: true,  // Convert line breaks to <br>
                gfm: true      // GitHub Flavored Markdown
            });
            return marked.parse(text);
        }
        // Fallback: basic markdown replacement
        return text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    };

    /**
     * Render HTML content from Markdown safely
     */
    window.renderMarkdown = function(elementId, text, defaultText = '') {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        const content = text || defaultText;
        el.innerHTML = window.parseMarkdown(content);
    };

    /**
     * Show typing indicator
     */
    window.showTypingIndicator = function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Remove existing typing indicator
        const existing = container.querySelector('.typing-indicator');
        if (existing) existing.remove();
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
        indicator.style.cssText = `
            display: flex;
            gap: 4px;
            padding: 10px 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            width: fit-content;
            margin: 10px 0;
        `;
        
        const dots = indicator.querySelectorAll('.typing-dot');
        dots.forEach((dot, i) => {
            dot.style.cssText = `
                width: 8px;
                height: 8px;
                background: #4299e1;
                border-radius: 50%;
                animation: typingBounce 1.4s ease-in-out infinite;
                animation-delay: ${i * 0.2}s;
            `;
        });
        
        // Add animation keyframes if not exists
        if (!document.getElementById('typing-styles')) {
            const style = document.createElement('style');
            style.id = 'typing-styles';
            style.textContent = `
                @keyframes typingBounce {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-8px); }
                }
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .response-fade-in {
                    animation: fadeInUp 0.4s ease-out forwards;
                }
            `;
            document.head.appendChild(style);
        }
        
        container.appendChild(indicator);
    };

    /**
     * Hide typing indicator
     */
    window.hideTypingIndicator = function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const indicator = container.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    };

    /**
     * Show response with fade-in animation
     */
    window.showResponse = function(elementId, htmlContent) {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        el.innerHTML = htmlContent;
        el.classList.add('response-fade-in');
        
        // Apply fade-in to child elements for smoother effect
        setTimeout(() => {
            el.classList.remove('response-fade-in');
        }, 400);
    };

    /**
     * Show loading indicator
     */
    window.showLoading = function(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.classList.add('loading');
            el.style.opacity = '0.5';
        }
    };

    /**
     * Hide loading indicator
     */
    window.hideLoading = function(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.classList.remove('loading');
            el.style.opacity = '1';
        }
    };

    /**
     * Show notification/alert
     */
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    };

    /**
     * Format date
     */
    window.formatDate = function(date) {
        const d = new Date(date);
        return d.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    /**
     * Format timestamp
     */
    window.formatTimestamp = function(date) {
        const d = new Date(date);
        return d.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    /**
     * Debounce function
     */
    window.debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    /**
     * Safe JSON parse
     */
    window.safeJsonParse = function(str, defaultValue = null) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.error('JSON parse error:', e);
            return defaultValue;
        }
    };

    /**
     * API helper
     */
    window.apiRequest = async function(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    };

    // ============================================
    // Animation Helpers
    // ============================================
    
    /**
     * Add fade-in animation to element
     */
    window.fadeIn = function(element, duration = 300) {
        const el = typeof element === 'string' ? document.getElementById(element) : element;
        if (!el) return;
        
        el.style.opacity = '0';
        el.style.display = 'block';
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            el.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    };

    /**
     * Add fade-out animation to element
     */
    window.fadeOut = function(element, duration = 300) {
        const el = typeof element === 'string' ? document.getElementById(element) : element;
        if (!el) return;
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.max(1 - progress / duration, 0);
            
            el.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                el.style.display = 'none';
            }
        }
        
        requestAnimationFrame(animate);
    };

    // ============================================
    // Global Functions (for backward compatibility)
    // ============================================
    
    // These functions might be called from inline handlers
    window.refreshPage = function() {
        window.location.reload();
    };

    window.scrollToElement = function(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth' });
        }
    };

    window.toggleElement = function(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }
    };

    // Export for use in modules
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            AppState: window.AppState,
            showLoading: window.showLoading,
            hideLoading: window.hideLoading,
            showNotification: window.showNotification,
            apiRequest: window.apiRequest
        };
    }

})();
