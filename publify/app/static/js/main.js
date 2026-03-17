// Publify main JavaScript

// CSRF token helper
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }

    // Try to find CSRF token in forms
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    if (csrfInput) {
        return csrfInput.value;
    }

    return '';
}

// Add CSRF token to all fetch requests
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
        options.headers = options.headers || {};

        // If headers is a Headers object, convert to plain object
        if (options.headers instanceof Headers) {
            const plainHeaders = {};
            options.headers.forEach((value, key) => {
                plainHeaders[key] = value;
            });
            options.headers = plainHeaders;
        }

        // Add CSRF token
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            options.headers['X-CSRF-Token'] = csrfToken;
        }
    }
    return originalFetch(url, options);
};

// Form validation helpers
function validatePasswordMatch(password, confirmPassword) {
    return password === confirmPassword;
}

function validateUsername(username) {
    return /^[a-zA-Z0-9_]{3,50}$/.test(username);
}

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#17a2b8'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Copy to clipboard helper
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'error');
        return false;
    }
}

// API helper for making authenticated requests
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error?.message || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Format date helper
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add CSRF token meta tag if not present
    if (!document.querySelector('meta[name="csrf-token"]')) {
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            const meta = document.createElement('meta');
            meta.name = 'csrf-token';
            meta.content = csrfInput.value;
            document.head.appendChild(meta);
        }
    }

    // Initialize form validations
    const registerForm = document.querySelector('form[action="/auth/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = this.querySelector('#password').value;
            const confirmPassword = this.querySelector('#confirm_password').value;

            if (password && confirmPassword && password !== confirmPassword) {
                e.preventDefault();
                showToast('Passwords do not match', 'error');
            }
        });
    }
});

// Export for use in other scripts
window.Publify = {
    showToast,
    copyToClipboard,
    apiCall,
    formatDate,
    debounce,
    getCSRFToken,
};
