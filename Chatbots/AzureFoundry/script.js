document.addEventListener('DOMContentLoaded', () => {
  // Chat Widget Elements
  const chatTrigger = document.getElementById('chat-trigger');
  const chatWidget = document.getElementById('chat-widget');
  const chatToggle = document.getElementById('chat-toggle');
  const chatBody = document.getElementById('chat-body');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('user-input');
  const chatBox = document.getElementById('chat-box');
  
  let isProcessing = false;
  let isChatOpen = false;

  // Add status indicator and clear button to chat widget
  const statusDiv = document.createElement('div');
  statusDiv.className = 'status-indicator';
  statusDiv.style.display = 'none';
  chatBody.insertBefore(statusDiv, form);

  const clearButton = document.createElement('button');
  clearButton.textContent = 'Clear Chat';
  clearButton.className = 'clear-button';
  chatBody.insertBefore(clearButton, form);

  // Chat Widget Toggle Functions
  function openChat() {
    chatWidget.classList.add('open');
    chatTrigger.style.display = 'none';
    isChatOpen = true;
    setTimeout(() => input.focus(), 100);
  }

  function closeChat() {
    chatWidget.classList.remove('open');
    chatTrigger.style.display = 'block';
    isChatOpen = false;
  }

  // Event Listeners for Chat Widget
  chatTrigger.addEventListener('click', openChat);
  chatToggle.addEventListener('click', closeChat);

  // Close chat when clicking outside
  document.addEventListener('click', (e) => {
    if (isChatOpen && !chatWidget.contains(e.target) && e.target !== chatTrigger) {
      closeChat();
    }
  });

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

  // Chat Form Handler
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
      typingIndicator.style.opacity = '0';
      await new Promise(resolve => setTimeout(resolve, 300));
      typingIndicator.textContent = data.reply;
      typingIndicator.classList.remove('typing');
      typingIndicator.style.opacity = '1';
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

  // Bookstore Functionality
  let cartCount = 0;
  const cartCountElement = document.querySelector('.cart-count');

  // Add to Cart functionality
  document.querySelectorAll('.add-to-cart-btn').forEach(button => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      const bookCard = e.target.closest('.book-card');
      const bookTitle = bookCard.querySelector('h3').textContent;
      
      // Animate button
      button.style.background = '#27ae60';
      button.textContent = 'Added!';
      
      // Update cart count
      cartCount++;
      cartCountElement.textContent = cartCount;
      cartCountElement.style.animation = 'bounce 0.5s ease';
      
      // Show notification
      showNotification(`"${bookTitle}" added to cart!`);
      
      // Reset button after 2 seconds
      setTimeout(() => {
        button.style.background = '#3498db';
        button.textContent = 'Add to Cart';
      }, 2000);
      
      // Remove animation
      setTimeout(() => {
        cartCountElement.style.animation = '';
      }, 500);
    });
  });

  // Search functionality
  const heroSearchBtn = document.querySelector('.hero-search-btn');
  const heroSearchInput = document.querySelector('.hero-search-input');
  const headerSearchBtn = document.querySelector('.search-btn');

  function handleSearch() {
    const searchTerm = heroSearchInput.value.trim();
    if (searchTerm) {
      showNotification(`Searching for "${searchTerm}"...`);
      // In a real app, this would trigger actual search functionality
    }
  }

  heroSearchBtn.addEventListener('click', handleSearch);
  headerSearchBtn.addEventListener('click', () => {
    heroSearchInput.focus();
  });

  heroSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  });

  // Newsletter subscription
  const newsletterForm = document.querySelector('.newsletter-form');
  newsletterForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = e.target.querySelector('.newsletter-input').value;
    if (email) {
      showNotification('Thank you for subscribing to our newsletter!');
      e.target.querySelector('.newsletter-input').value = '';
    }
  });

  // Category card interactions
  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
      const categoryName = card.querySelector('h3').textContent;
      showNotification(`Browsing ${categoryName} books...`);
    });
  });

  // Smooth scrolling for navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      if (targetId && targetId.startsWith('#') && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // Notification system
  function showNotification(message) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #2c3e50;
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      z-index: 10000;
      font-size: 0.9rem;
      max-width: 300px;
      opacity: 0;
      transform: translateX(100%);
      transition: all 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.style.opacity = '1';
      notification.style.transform = 'translateX(0)';
    }, 10);

    // Animate out and remove
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // Add bounce animation for cart
  const style = document.createElement('style');
  style.textContent = `
    @keyframes bounce {
      0%, 20%, 60%, 100% {
        transform: translateY(0);
      }
      40% {
        transform: translateY(-10px);
      }
      80% {
        transform: translateY(-5px);
      }
    }
  `;
  document.head.appendChild(style);

  // Initialize chat with welcome message
  setTimeout(() => {
    if (chatBox.children.length === 0) {
      appendMessage('bot', 'Hello! I\'m your BookHaven assistant. How can I help you find your next great read today?');
    }
  }, 1000);
});
