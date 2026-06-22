// AgriSense App.JS - Native Webview Desktop Bridge

let selectedImageDataUrl = null;
let isGenerating = false;
let activeAiMessageDiv = null;
let activeAiTextContent = "";

// Wait for pywebview API to load
window.addEventListener('pywebviewready', () => {
  initApp();
});

// Fallback in case event already fired
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (window.pywebview && !isInitialized) {
      initApp();
    }
  }, 100);
});

let isInitialized = false;

function initApp() {
  if (isInitialized) return;
  isInitialized = true;

  // Perform initial Ollama connection check
  checkOllamaStatus();
  
  // Set up repeating check for status every 10 seconds
  setInterval(checkOllamaStatus, 10000);

  // Set up event listeners
  setupEventListeners();
}

// Check if local Ollama server is running and model is loaded
function checkOllamaStatus() {
  if (!window.pywebview || !window.pywebview.api) return;

  const statusDot = document.getElementById('status-dot');
  const statusLabel = document.getElementById('status-label');
  const statusDetails = document.getElementById('status-details');
  const statusCard = document.getElementById('status-card');

  window.pywebview.api.check_ollama_status()
    .then(result => {
      if (result.running) {
        statusDot.className = 'status-dot connected';
        statusLabel.textContent = 'Ollama Connected';
        statusCard.className = 'status-card connected';
        statusDetails.textContent = `Model loaded: ${result.model || 'qwen2.5:1.5b'}`;
      } else {
        statusDot.className = 'status-dot offline';
        statusLabel.textContent = 'Ollama Offline';
        statusCard.className = 'status-card';
        statusDetails.innerHTML = 'Ollama is not running. Please run <code style="background: rgba(255,255,255,0.1); padding: 1px 4px; border-radius: 3px;">ollama serve</code> in your terminal.';
      }
    })
    .catch(err => {
      console.error('Error checking Ollama status:', err);
      statusDot.className = 'status-dot offline';
      statusLabel.textContent = 'Connection Error';
      statusCard.className = 'status-card';
      statusDetails.textContent = 'Could not communicate with Python backend.';
    });
}

function setupEventListeners() {
  const form = document.getElementById('input-form');
  const textarea = document.getElementById('chat-input');
  const imageInput = document.getElementById('image-input');
  const removeImageBtn = document.getElementById('remove-image-btn');
  const clearBtn = document.getElementById('clear-btn');
  const suggestionButtons = document.querySelectorAll('.suggestion-btn');

  // Auto-resize textarea as farmer types
  textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight - 4) + 'px';
  });

  // Submit form on Enter key (unless Shift is held)
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });

  // Handle image file selection
  imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      selectedImageDataUrl = event.target.result;
      
      // Update UI preview
      const previewImg = document.getElementById('image-preview');
      const previewContainer = document.getElementById('image-preview-container');
      const filenameSpan = document.getElementById('preview-filename');
      
      previewImg.src = selectedImageDataUrl;
      filenameSpan.textContent = file.name;
      previewContainer.classList.remove('hidden');
      
      // Scroll input panel into view if needed
      previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };
    reader.readAsDataURL(file);
  });

  // Remove attached image
  removeImageBtn.addEventListener('click', () => {
    clearImageAttachment();
  });

  // Submit Query
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (isGenerating) return;

    const userText = textarea.value.trim();
    if (!userText && !selectedImageDataUrl) return;

    submitQuery(userText, selectedImageDataUrl);
  });

  // Clear Chat history
  clearBtn.addEventListener('click', () => {
    if (confirm("Are you sure you want to clear this conversation?")) {
      clearChat();
    }
  });

  // Setup common queries triggers
  suggestionButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      textarea.value = query;
      textarea.style.height = 'auto';
      textarea.style.height = (textarea.scrollHeight - 4) + 'px';
      textarea.focus();
    });
  });

  // Setup streaming bridge listeners
  window.addEventListener('agrisense:stream_start', handleStreamStart);
  window.addEventListener('agrisense:stream_token', handleStreamToken);
  window.addEventListener('agrisense:stream_end', handleStreamEnd);
  window.addEventListener('agrisense:stream_error', handleStreamError);
}

function clearImageAttachment() {
  selectedImageDataUrl = null;
  document.getElementById('image-input').value = '';
  document.getElementById('image-preview-container').classList.add('hidden');
  document.getElementById('image-preview').src = '';
}

function clearChat() {
  const container = document.getElementById('messages-container');
  // Preserve welcome message, delete others
  const welcomeMessage = container.firstElementChild;
  container.innerHTML = '';
  if (welcomeMessage) {
    container.appendChild(welcomeMessage);
  }
}

// Submit prompt to backend via stream
function submitQuery(text, imageBase64) {
  isGenerating = true;
  
  // Disable interface
  const textarea = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  textarea.disabled = true;
  sendBtn.disabled = true;

  // Append user bubble to chat window
  appendUserMessage(text, imageBase64);

  // Append temporary empty AI bubble with skeleton loader
  appendAiSkeleton();

  // Scroll to bottom
  scrollToBottom();

  // Call pywebview python API
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.handle_query_stream(text, imageBase64)
      .then(res => {
        if (!res.started) {
          showSystemError("Failed to initiate offline request.");
          enableInput();
        }
      })
      .catch(err => {
        showSystemError("Bridge Error: " + err);
        enableInput();
      });
  } else {
    showSystemError("AgriSense API bridge not initialized. Restart the application.");
    enableInput();
  }

  // Clear inputs
  textarea.value = '';
  textarea.style.height = 'auto';
  clearImageAttachment();
}

function enableInput() {
  isGenerating = false;
  const textarea = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  textarea.disabled = false;
  sendBtn.disabled = false;
  document.getElementById('stream-info-bar').classList.add('hidden');
  textarea.focus();
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  container.scrollTop = container.scrollHeight;
}

function appendUserMessage(text, imageBase64) {
  const container = document.getElementById('messages-container');
  
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message farmer';

  // Avatar
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;

  // Content wrapper
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  if (text) {
    const p = document.createElement('p');
    p.textContent = text;
    contentDiv.appendChild(p);
  }

  if (imageBase64) {
    const img = document.createElement('img');
    img.src = imageBase64;
    img.className = 'message-attached-image';
    contentDiv.appendChild(img);
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);
}

function appendAiSkeleton() {
  const container = document.getElementById('messages-container');
  
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message ai';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C6.5 2 2 6.5 2 12c0 3.5 1.8 6.6 4.5 8.4l1.5-1.5C6 17.5 5 14.9 5 12c0-3.9 3.1-7 7-7s7 3.1 7 7c0 2.9-1 5.5-3 6.9l1.5 1.5c2.7-1.8 4.5-4.9 4.5-8.4 0-5.5-4.5-10-10-10z"/></svg>`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.id = 'active-ai-content';
  
  contentDiv.innerHTML = `
    <div class="skeleton">
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
    </div>
  `;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);

  activeAiMessageDiv = contentDiv;
  activeAiTextContent = "";
}

function showSystemError(messageText) {
  const container = document.getElementById('messages-container');
  
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message ai system-error';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.style.backgroundColor = '#E07A5F';
  avatar.innerHTML = `⚠️`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.innerHTML = `<p><strong>System Alert:</strong> ${messageText}</p>`;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);
  
  if (activeAiMessageDiv && activeAiMessageDiv.innerHTML.includes('skeleton')) {
    activeAiMessageDiv.parentElement.remove();
  }
  
  scrollToBottom();
}

// Event Handlers for streaming custom events
function handleStreamStart(e) {
  const data = e.detail;
  const infoBar = document.getElementById('stream-info-bar');
  const statusText = document.getElementById('stream-status-text');

  infoBar.classList.remove('hidden');
  statusText.textContent = "AgriSense is generating answer...";

  if (activeAiMessageDiv) {
    // Clear skeleton
    activeAiMessageDiv.innerHTML = '';

    // Prepend Vision Tag if disease was classified
    if (data && data.visionTag) {
      const tagSpan = document.createElement('div');
      tagSpan.className = 'vision-tag';
      tagSpan.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
        <span>${data.visionTag}</span>
      `;
      activeAiMessageDiv.appendChild(tagSpan);
    }

    // Add streaming text placeholder
    const textSpan = document.createElement('span');
    textSpan.id = 'streaming-text-block';
    activeAiMessageDiv.appendChild(textSpan);
  }
}

function handleStreamToken(e) {
  const data = e.detail;
  const textSpan = document.getElementById('streaming-text-block');
  
  if (textSpan) {
    activeAiTextContent += data.token;
    // Replace newline with br for intermediate streaming
    textSpan.innerHTML = activeAiTextContent.replace(/\n/g, '<br>');
    scrollToBottom();
  }
}

function handleStreamEnd(e) {
  const textSpan = document.getElementById('streaming-text-block');
  if (activeAiMessageDiv && textSpan) {
    // Convert full streamed context to markdown parsed html on end
    const htmlContent = parseMarkdown(activeAiTextContent);
    
    // Preserve the vision tag if it existed
    const visionTag = activeAiMessageDiv.querySelector('.vision-tag');
    activeAiMessageDiv.innerHTML = '';
    
    if (visionTag) {
      activeAiMessageDiv.appendChild(visionTag);
    }
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = htmlContent;
    activeAiMessageDiv.appendChild(wrapper);
  }

  // Cleanup
  activeAiMessageDiv = null;
  activeAiTextContent = "";
  enableInput();
  scrollToBottom();
}

function handleStreamError(e) {
  const data = e.detail;
  showSystemError(data.message || "An unknown retrieval error occurred.");
  enableInput();
}

// Simple Offline-Safe Markdown Parser
function parseMarkdown(text) {
  let html = text;

  // Escape HTML entities to prevent XSS
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Headers
  html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');

  // Bullet list items
  html = html.replace(/^\s*[-*+]\s+(.*?)$/gm, '<li>$1</li>');
  
  // Wrap list items in ul
  html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');

  // Paragraphs split by double linebreaks, and single linebreaks handled
  let parts = html.split(/\n\n+/);
  html = parts.map(part => {
    // If it's a list or header, don't wrap in p tag
    if (part.startsWith('<ul>') || part.startsWith('<h3>') || part.startsWith('<h2>') || part.startsWith('<h1>')) {
      return part.replace(/\n/g, '<br>');
    }
    return `<p>${part.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}
