// GreenNet App.JS - Native Webview Desktop Bridge

let selectedImageDataUrl = null;
let isGenerating = false;
let activeAiMessageDiv = null;
let activeAiTextContent = "";

// Skeleton state
let rotatingMessageInterval = null;
let firstTokenReceived = false;
let pendingVisionTag = null;

// ── Psychological reassurance messages ─────────────────────────────────────
// Phase 1: between submit and stream_start (vision + RAG + DB lookup happening)
const PRE_STREAM_MESSAGES = [
  "Scanning your crop knowledge base...",
  "Checking pest & disease records...",
  "Analyzing agricultural context...",
  "Retrieving local market data...",
  "Cross-referencing treatment database...",
  "Preparing your personalized advice...",
];

// Phase 2: between stream_start and first token (Ollama model generating)
const GENERATING_MESSAGES = [
  "GreenNet is composing your answer...",
  "Local AI model is thinking...",
  "Writing your farming advice now...",
  "Almost there — final touches...",
  "Tailoring response to your query...",
];

// ── Init ───────────────────────────────────────────────────────────────────
window.addEventListener('pywebviewready', () => { initApp(); });

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (window.pywebview && !isInitialized) { initApp(); }
  }, 100);
});

let isInitialized = false;

function initApp() {
  if (isInitialized) return;
  isInitialized = true;
  checkOllamaStatus();
  setInterval(checkOllamaStatus, 10000);
  setupEventListeners();
}

// ── Ollama health check ────────────────────────────────────────────────────
function checkOllamaStatus() {
  if (!window.pywebview || !window.pywebview.api) return;

  const statusDot     = document.getElementById('status-dot');
  const statusLabel   = document.getElementById('status-label');
  const statusDetails = document.getElementById('status-details');
  const statusCard    = document.getElementById('status-card');

  window.pywebview.api.check_ollama_status()
    .then(result => {
      if (result.running) {
        statusDot.className    = 'status-dot connected';
        statusLabel.textContent = 'Ollama Connected';
        statusCard.className   = 'status-card connected';
        statusDetails.textContent = `Model loaded: ${result.model || 'qwen2.5:1.5b'}`;
      } else {
        statusDot.className    = 'status-dot offline';
        statusLabel.textContent = 'Ollama Offline';
        statusCard.className   = 'status-card';
        statusDetails.innerHTML = 'Ollama not running. Run <code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:3px;">ollama serve</code> in your terminal.';
      }
    })
    .catch(() => {
      statusDot.className    = 'status-dot offline';
      statusLabel.textContent = 'Connection Error';
      statusCard.className   = 'status-card';
      statusDetails.textContent = 'Could not communicate with Python backend.';
    });
}

// ── Event listeners ────────────────────────────────────────────────────────
function setupEventListeners() {
  const form           = document.getElementById('input-form');
  const textarea       = document.getElementById('chat-input');
  const imageInput     = document.getElementById('image-input');
  const removeImageBtn = document.getElementById('remove-image-btn');
  const clearBtn       = document.getElementById('clear-btn');
  const suggestionBtns = document.querySelectorAll('.suggestion-btn');

  // Auto-resize textarea
  textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight - 4) + 'px';
  });

  // Enter to submit (Shift+Enter = newline)
  textarea.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });

  // Image file selection → base64
  imageInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = event => {
      selectedImageDataUrl = event.target.result;
      document.getElementById('image-preview').src = selectedImageDataUrl;
      document.getElementById('preview-filename').textContent = file.name;
      document.getElementById('image-preview-container').classList.remove('hidden');
      document.getElementById('image-preview-container').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };
    reader.readAsDataURL(file);
  });

  removeImageBtn.addEventListener('click', clearImageAttachment);

  // Form submit
  form.addEventListener('submit', e => {
    e.preventDefault();
    if (isGenerating) return;
    const userText = textarea.value.trim();
    if (!userText && !selectedImageDataUrl) return;
    submitQuery(userText, selectedImageDataUrl);
  });

  // Clear chat
  clearBtn.addEventListener('click', () => {
    if (confirm("Are you sure you want to clear this conversation?")) clearChat();
  });

  // Suggestion buttons fill textarea
  suggestionBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      textarea.value = query;
      textarea.style.height = 'auto';
      textarea.style.height = (textarea.scrollHeight - 4) + 'px';
      textarea.focus();
    });
  });

  // Stream event bridge from Python → pywebview
  window.addEventListener('agrisense:stream_start', handleStreamStart);
  window.addEventListener('agrisense:stream_token', handleStreamToken);
  window.addEventListener('agrisense:stream_end',   handleStreamEnd);
  window.addEventListener('agrisense:stream_error', handleStreamError);
}

// ── Rotating skeleton message helpers ─────────────────────────────────────
function startRotatingMessages(messages) {
  stopRotatingMessages(); // clear any existing interval
  let index = 0;
  _updateSkeletonLabel(messages[0]);

  rotatingMessageInterval = setInterval(() => {
    index = (index + 1) % messages.length;
    const label = document.getElementById('skeleton-status-text');
    if (!label) { stopRotatingMessages(); return; }

    // Smooth fade-out → change text → fade-in
    label.style.opacity = '0';
    label.style.transform = 'translateY(4px)';
    setTimeout(() => {
      if (document.getElementById('skeleton-status-text')) {
        label.textContent = messages[index];
        label.style.opacity = '1';
        label.style.transform = 'translateY(0)';
      }
    }, 220);
  }, 2400);
}

function stopRotatingMessages() {
  if (rotatingMessageInterval) {
    clearInterval(rotatingMessageInterval);
    rotatingMessageInterval = null;
  }
}

function _updateSkeletonLabel(text) {
  const label = document.getElementById('skeleton-status-text');
  if (label) label.textContent = text;
}

// ── Query submission ───────────────────────────────────────────────────────
function submitQuery(text, imageBase64) {
  isGenerating = true;
  firstTokenReceived = false;
  pendingVisionTag = null;

  // Disable UI
  const textarea = document.getElementById('chat-input');
  const sendBtn  = document.getElementById('send-btn');
  textarea.disabled = true;
  sendBtn.disabled  = true;

  appendUserMessage(text, imageBase64);
  appendAiSkeleton();         // Shows skeleton + starts Phase-1 messages
  scrollToBottom();

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.handle_query_stream(text, imageBase64)
      .then(res => {
        if (!res.started) { showSystemError("Failed to initiate offline request."); enableInput(); }
      })
      .catch(err => {
        showSystemError("Bridge Error: " + err);
        enableInput();
      });
  } else {
    showSystemError("GreenNet API bridge not initialized. Restart the application.");
    enableInput();
  }

  textarea.value = '';
  textarea.style.height = 'auto';
  clearImageAttachment();
}

function enableInput() {
  isGenerating = false;
  stopRotatingMessages();
  const textarea = document.getElementById('chat-input');
  const sendBtn  = document.getElementById('send-btn');
  textarea.disabled = false;
  sendBtn.disabled  = false;
  textarea.focus();
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  container.scrollTop = container.scrollHeight;
}

// ── DOM helpers ────────────────────────────────────────────────────────────
function clearImageAttachment() {
  selectedImageDataUrl = null;
  document.getElementById('image-input').value = '';
  document.getElementById('image-preview-container').classList.add('hidden');
  document.getElementById('image-preview').src = '';
}

function clearChat() {
  const container = document.getElementById('messages-container');
  const welcome = container.firstElementChild;
  container.innerHTML = '';
  if (welcome) container.appendChild(welcome);
}

function appendUserMessage(text, imageBase64) {
  const container = document.getElementById('messages-container');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message farmer';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;

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
    <div class="skeleton-status-label">
      <span class="skeleton-pulse-dot"></span>
      <span id="skeleton-status-text">Scanning your crop knowledge base...</span>
    </div>
  `;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);

  activeAiMessageDiv = contentDiv;
  activeAiTextContent = "";

  // Start Phase-1 rotating messages immediately
  startRotatingMessages(PRE_STREAM_MESSAGES);
}

function showSystemError(messageText) {
  const container = document.getElementById('messages-container');
  stopRotatingMessages();

  // Remove dangling skeleton if present
  if (activeAiMessageDiv) {
    activeAiMessageDiv.parentElement.remove();
    activeAiMessageDiv = null;
  }

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
  scrollToBottom();
}

// ── Stream event handlers ──────────────────────────────────────────────────

// stream_start → Python finished context gathering, Ollama is now generating.
// Switch to Phase-2 messages but KEEP the skeleton visible.
function handleStreamStart(e) {
  pendingVisionTag = e.detail?.visionTag || null;
  // Switch message set to reflect model is now writing
  startRotatingMessages(GENERATING_MESSAGES);
}

// stream_token → First actual token means model has produced output.
// Replace skeleton with real content only now.
function handleStreamToken(e) {
  const token = e.detail.token;

  if (!firstTokenReceived) {
    firstTokenReceived = true;
    stopRotatingMessages();

    if (activeAiMessageDiv) {
      activeAiMessageDiv.innerHTML = '';

      // Vision tag (if image was diagnosed)
      if (pendingVisionTag) {
        const tagDiv = document.createElement('div');
        tagDiv.className = 'vision-tag';
        tagDiv.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          <span>${pendingVisionTag}</span>
        `;
        activeAiMessageDiv.appendChild(tagDiv);
      }

      // Streaming text container
      const textSpan = document.createElement('span');
      textSpan.id = 'streaming-text-block';
      activeAiMessageDiv.appendChild(textSpan);
    }

    activeAiTextContent = token;
  } else {
    activeAiTextContent += token;
  }

  const textSpan = document.getElementById('streaming-text-block');
  if (textSpan) {
    textSpan.innerHTML = activeAiTextContent.replace(/\n/g, '<br>');
    scrollToBottom();
  }
}

// stream_end → Swap raw streamed text for rendered markdown
function handleStreamEnd() {
  const textSpan = document.getElementById('streaming-text-block');
  if (activeAiMessageDiv && textSpan) {
    const htmlContent = parseMarkdown(activeAiTextContent);
    const visionTag = activeAiMessageDiv.querySelector('.vision-tag');
    activeAiMessageDiv.innerHTML = '';
    if (visionTag) activeAiMessageDiv.appendChild(visionTag);
    const wrapper = document.createElement('div');
    wrapper.innerHTML = htmlContent;
    activeAiMessageDiv.appendChild(wrapper);
  }

  activeAiMessageDiv = null;
  activeAiTextContent = "";
  enableInput();
  scrollToBottom();
}

function handleStreamError(e) {
  stopRotatingMessages();
  showSystemError(e.detail?.message || "An unknown error occurred.");
  enableInput();
}

// ── Simple offline-safe Markdown parser ───────────────────────────────────
function parseMarkdown(text) {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
  html = html.replace(/^\s*[-*+]\s+(.*?)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');

  const parts = html.split(/\n\n+/);
  html = parts.map(part => {
    if (part.startsWith('<ul>') || /^<h[123]>/.test(part)) {
      return part.replace(/\n/g, '<br>');
    }
    return `<p>${part.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}
