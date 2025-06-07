document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('user-input');
  const chatBox = document.getElementById('chat-box');
  let isProcessing = false;

  // Add status indicator
  const statusDiv = document.createElement('div');
  statusDiv.className = 'status-indicator';
  statusDiv.style.display = 'none';
  form.parentNode.insertBefore(statusDiv, form);

  // Add clear conversation button
  const clearButton = document.createElement('button');
  clearButton.textContent = 'Clear Chat';
  clearButton.className = 'clear-button';
  form.parentNode.insertBefore(clearButton, form);

  // Network status handler
  window.addEventListener('online', () => updateStatus('Connected'));
  window.addEventListener('offline', () => updateStatus('Offline', true));

  function updateStatus(message, isError = false) {
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    statusDiv.className = `status-indicator ${isError ? 'error' : 'success'}`;
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 3000);
  }

  clearButton.addEventListener('click', async () => {
    try {
      await fetch('/clear', { method: 'POST' });
      chatBox.innerHTML = '';
      updateStatus('Chat cleared');
    } catch (error) {
      console.error('Failed to clear chat history:', error);
      updateStatus('Failed to clear chat', true);
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isProcessing) return;

    const userMessage = input.value.trim();
    if (!userMessage) return;

    isProcessing = true;
    input.disabled = true;
    appendMessage('user', userMessage);
    input.value = '';
    
    const typingIndicator = appendMessage('bot', '...');
    typingIndicator.classList.add('typing');
    
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.reply || `Server error: ${response.status}`);
      }

      const data = await response.json();
      typingIndicator.style.opacity = '0';  // Start fade out
      await new Promise(resolve => setTimeout(resolve, 300));  // Wait for fade
      typingIndicator.textContent = data.reply;
      typingIndicator.classList.remove('typing');
      typingIndicator.style.opacity = '1';  // Fade in the response
    } catch (error) {
      typingIndicator.style.opacity = '0';
      await new Promise(resolve => setTimeout(resolve, 300));
      typingIndicator.textContent = `Error: ${error.message}`;
      typingIndicator.classList.remove('typing');
      typingIndicator.classList.add('error');
      typingIndicator.style.opacity = '1';
      updateStatus('Failed to send message', true);
    } finally {
      isProcessing = false;
      input.disabled = false;
      input.focus();
    }
  });

  function appendMessage(sender, message) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message', `${sender}-message`);
    msgDiv.textContent = message;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msgDiv;
  }
});
