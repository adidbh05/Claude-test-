/**
 * Eurocode 3 Structural Design Chat Application
 * Frontend JavaScript
 */

// ============== Configuration ==============
const API_BASE = '/api';
const MAX_MESSAGE_LENGTH = 4000;

// ============== State ==============
let currentConversationId = null;
let isLoading = false;

// ============== DOM Elements ==============
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    conversationsList: document.getElementById('conversationsList'),
    pageTitle: document.getElementById('pageTitle'),
    chatContainer: document.getElementById('chatContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    rateLimitText: document.getElementById('rateLimitText'),
    toastContainer: document.getElementById('toastContainer'),
    steelGrade: document.getElementById('steelGrade')
};

// ============== Initialization ==============
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    loadConversations();
    updateRateLimitInfo();
    autoResizeTextarea();

    // Initialize KaTeX auto-render if available
    if (typeof renderMathInElement !== 'undefined') {
        document.addEventListener('DOMContentLoaded', () => {
            renderMathInElement(document.body, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                    { left: '\\[', right: '\\]', display: true },
                    { left: '\\(', right: '\\)', display: false }
                ]
            });
        });
    }
}

// ============== Event Listeners ==============
function setupEventListeners() {
    // Sidebar toggle
    elements.sidebarToggle?.addEventListener('click', toggleSidebar);
    elements.mobileMenuBtn?.addEventListener('click', toggleSidebar);

    // New chat
    elements.newChatBtn?.addEventListener('click', startNewChat);

    // Message input
    elements.messageInput?.addEventListener('input', handleInputChange);
    elements.messageInput?.addEventListener('keydown', handleKeyDown);

    // Send button
    elements.sendBtn?.addEventListener('click', sendMessage);

    // Quick action cards
    document.querySelectorAll('.action-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.dataset.prompt;
            if (prompt) {
                elements.messageInput.value = prompt;
                handleInputChange();
                sendMessage();
            }
        });
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            elements.sidebar.classList.contains('open') &&
            !elements.sidebar.contains(e.target) &&
            e.target !== elements.mobileMenuBtn) {
            elements.sidebar.classList.remove('open');
        }
    });
}

// ============== Sidebar Functions ==============
function toggleSidebar() {
    elements.sidebar.classList.toggle('open');
}

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/conversations`);
        if (!response.ok) throw new Error('Failed to load conversations');

        const conversations = await response.json();
        renderConversationsList(conversations);
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

function renderConversationsList(conversations) {
    if (!conversations.length) {
        elements.conversationsList.innerHTML = `
            <div class="empty-state" style="padding: 1rem; color: var(--text-muted); font-size: 0.875rem; text-align: center;">
                No conversations yet
            </div>
        `;
        return;
    }

    elements.conversationsList.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.conversation_id === currentConversationId ? 'active' : ''}"
             data-id="${conv.conversation_id}"
             onclick="loadConversation('${conv.conversation_id}')">
            <i class="fas fa-ruler-combined"></i>
            <span class="title">${escapeHtml(conv.title)}</span>
            <button class="delete-btn" onclick="event.stopPropagation(); deleteConversation('${conv.conversation_id}')" title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// ============== Conversation Functions ==============
function startNewChat() {
    currentConversationId = null;
    elements.pageTitle.textContent = 'New Calculation';
    elements.messagesContainer.innerHTML = '';
    elements.messagesContainer.classList.remove('active');
    elements.welcomeScreen.classList.remove('hidden');
    elements.messageInput.value = '';
    handleInputChange();

    // Update active state in sidebar
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });

    // Close mobile sidebar
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.remove('open');
    }
}

async function loadConversation(conversationId) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
        if (!response.ok) throw new Error('Failed to load conversation');

        const conversation = await response.json();
        currentConversationId = conversationId;

        // Update UI
        elements.pageTitle.textContent = conversation.title || 'Calculation';
        elements.welcomeScreen.classList.add('hidden');
        elements.messagesContainer.classList.add('active');

        // Render messages
        renderMessages(conversation.messages);

        // Update sidebar active state
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === conversationId);
        });

        // Close mobile sidebar
        if (window.innerWidth <= 768) {
            elements.sidebar.classList.remove('open');
        }

    } catch (error) {
        console.error('Error loading conversation:', error);
        showToast('Failed to load conversation', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteConversation(conversationId) {
    if (!confirm('Delete this conversation?')) return;

    try {
        const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete conversation');

        // Refresh list
        await loadConversations();

        // If deleted current conversation, start new chat
        if (conversationId === currentConversationId) {
            startNewChat();
        }

        showToast('Conversation deleted', 'success');
    } catch (error) {
        console.error('Error deleting conversation:', error);
        showToast('Failed to delete conversation', 'error');
    }
}

// ============== Message Functions ==============
function renderMessages(messages) {
    elements.messagesContainer.innerHTML = messages.map(msg => createMessageHTML(msg)).join('');
    scrollToBottom();
    renderMath();
}

function createMessageHTML(message) {
    const isUser = message.role === 'user';
    const avatarIcon = isUser ? 'fa-user' : 'fa-robot';
    const content = isUser ? escapeHtml(message.content) : formatMarkdown(message.content);

    return `
        <div class="message ${message.role}">
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">${content}</div>
            </div>
        </div>
    `;
}

function addMessage(role, content) {
    const messageHTML = createMessageHTML({ role, content });
    elements.messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
    renderMath();
}

// ============== Send Message ==============
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || isLoading) return;

    // Update UI
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('active');

    // Add user message
    addMessage('user', message);

    // Clear input
    elements.messageInput.value = '';
    handleInputChange();

    // Send to API
    try {
        isLoading = true;
        elements.sendBtn.disabled = true;
        showLoading();

        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });

        if (response.status === 429) {
            const errorData = await response.json();
            throw new Error(`Rate limit exceeded. Please wait ${Math.ceil(errorData.retry_after || 60)} seconds.`);
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to send message');
        }

        const data = await response.json();

        // Update conversation ID if new
        if (!currentConversationId) {
            currentConversationId = data.conversation_id;
            await loadConversations();
        }

        // Add assistant response
        addMessage('assistant', data.response);

        // Update rate limit info from headers
        const remaining = response.headers.get('X-RateLimit-Remaining-Minute');
        if (remaining) {
            elements.rateLimitText.textContent = `${remaining} requests remaining`;
        }

    } catch (error) {
        console.error('Error sending message:', error);
        showToast(error.message || 'Failed to send message', 'error');

        // Add error message to chat
        addMessage('assistant', `Sorry, an error occurred: ${error.message}. Please try again.`);
    } finally {
        isLoading = false;
        elements.sendBtn.disabled = false;
        hideLoading();
        handleInputChange();
    }
}

// ============== Input Handling ==============
function handleInputChange() {
    const hasContent = elements.messageInput.value.trim().length > 0;
    elements.sendBtn.disabled = !hasContent || isLoading;
    autoResizeTextarea();
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// ============== Rate Limit ==============
async function updateRateLimitInfo() {
    try {
        const response = await fetch(`${API_BASE}/rate-limit`);
        if (response.ok) {
            const data = await response.json();
            elements.rateLimitText.textContent = `${data.requests_remaining} requests remaining`;
        }
    } catch (error) {
        console.error('Error fetching rate limit:', error);
    }
}

// ============== UI Helpers ==============
function showLoading() {
    elements.loadingOverlay.classList.add('active');
}

function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

function showToast(message, type = 'info') {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    elements.toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ============== Text Formatting ==============
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // Use marked.js if available, otherwise basic formatting
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });
        return marked.parse(text);
    }

    // Basic markdown formatting fallback
    let html = escapeHtml(text);

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');

    // Lists
    html = html.replace(/^\- (.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    return html;
}

function renderMath() {
    // Render KaTeX math if available
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(elements.messagesContainer, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
                { left: '\\[', right: '\\]', display: true },
                { left: '\\(', right: '\\)', display: false }
            ],
            throwOnError: false
        });
    }
}

// ============== Expose functions globally ==============
window.loadConversation = loadConversation;
window.deleteConversation = deleteConversation;
