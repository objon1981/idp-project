// Service monitoring and interaction
const services = {
    ocr: { port: 8080, name: 'OCR Service' },
    llm: { port: 3001, name: 'Anything LLM' },
    docetl: { port: 5000, name: 'DocETL' },
    organizer: { port: 4000, name: 'File Organizer' },
    json: { port: 3000, name: 'JSON Crack' },
    kestra: { port: 8082, name: 'Kestra' },
    windmill: { port: 7780, name: 'Windmill' },
    localsend: { port: 5050, name: 'Local Send' },
    pake: { port: 8081, name: 'PAKE Security' },
    'email-router': { name: 'Email Router', port: 5001 }
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    checkAllServices();
    setupEventListeners();
    displayWelcomeMessage();
});

function setupEventListeners() {
    // Chat input handling
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Service card interactions
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('click', function() {
            const service = this.dataset.service;
            if (service) {
                showServiceDetails(service);
            }
        });
    });
}

async function checkAllServices() {
    for (const [serviceKey, serviceInfo] of Object.entries(services)) {
        await checkServiceStatus(serviceKey, serviceInfo.port);
    }
}

async function checkServiceStatus(serviceKey, port) {
    const statusElement = document.getElementById(`${serviceKey}-status`);
    const statusDot = statusElement.querySelector('.status-dot');
    const statusText = statusElement.querySelector('.status-text');

    try {
        // Try to check if service is responding
        const response = await fetch(`http://0.0.0.0:${port}/health`, {
            method: 'GET',
            timeout: 5000
        }).catch(() => null);

        if (response && response.ok) {
            statusDot.classList.add('online');
            statusText.textContent = 'Online';
        } else {
            statusDot.classList.add('offline');
            statusText.textContent = 'Offline';
        }
    } catch (error) {
        statusDot.classList.add('offline');
        statusText.textContent = 'Offline';
    }
}

async function testService(serviceKey, port) {
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Testing...';
    button.disabled = true;

    try {
        let testResult = false;

        switch (serviceKey) {
            case 'llm':
                testResult = await testLLMService(port);
                break;
            case 'ocr':
                testResult = await testOCRService(port);
                break;
            default:
                testResult = await testGenericService(port);
        }

        if (testResult) {
            showNotification(`${services[serviceKey].name} is working correctly!`, 'success');
        } else {
            showNotification(`${services[serviceKey].name} is not responding.`, 'error');
        }
    } catch (error) {
        showNotification(`Error testing ${services[serviceKey].name}: ${error.message}`, 'error');
    }

    button.textContent = originalText;
    button.disabled = false;
}

async function testLLMService(port) {
    try {
        const response = await fetch(`http://0.0.0.0:${port}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: 'Hello, this is a test message. Please respond briefly.'
            })
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function testOCRService(port) {
    try {
        const response = await fetch(`http://0.0.0.0:${port}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function testGenericService(port) {
    try {
        const response = await fetch(`http://0.0.0.0:${port}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai typing';
    typingDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> AI is thinking...';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        // Try to send to LLM service
        const response = await fetch('http://0.0.0.0:3001/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: message
            })
        });

        // Remove typing indicator
        chatMessages.removeChild(typingDiv);

        if (response.ok) {
            const data = await response.json();
            addMessage(data.answer || 'I received your message but could not generate a response.', 'ai');
        } else {
            addMessage('Sorry, the LLM service is currently unavailable. Please try again later.', 'ai');
        }
    } catch (error) {
        // Remove typing indicator
        chatMessages.removeChild(typingDiv);
        addMessage('Sorry, I cannot connect to the AI service right now. Please check if the service is running.', 'ai');
    }
}

function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function displayWelcomeMessage() {
    addMessage('Welcome to SOGUM AI! I can help you understand our document processing platform. Ask me anything about our services!', 'ai');
}

function showServiceDetails(serviceKey) {
    const service = services[serviceKey];
    if (!service) return;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${service.name}</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Port:</strong> ${service.port}</p>
                <p><strong>Status:</strong> <span id="modal-status">Checking...</span></p>
                <p><strong>Endpoint:</strong> http://0.0.0.0:${service.port}</p>
                <div class="modal-actions">
                    <button onclick="window.open('http://0.0.0.0:${service.port}', '_blank')" class="btn-primary">
                        Open Service
                    </button>
                    <button onclick="testService('${serviceKey}', ${service.port})" class="btn-secondary">
                        Test Connection
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Check status for modal
    checkServiceStatus(serviceKey, service.port).then(() => {
        const statusElement = document.getElementById(`${serviceKey}-status`);
        const modalStatus = document.getElementById('modal-status');
        if (modalStatus && statusElement) {
            modalStatus.textContent = statusElement.querySelector('.status-text').textContent;
        }
    });
}

function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        document.body.removeChild(modal);
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;

    // Add notification styles if not exists
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 1rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                animation: slideIn 0.3s ease;
            }
            .notification.success { background: #22c55e; }
            .notification.error { background: #ef4444; }
            .notification.info { background: #3b82f6; }
            .notification button {
                background: none;
                border: none;
                color: white;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0;
                margin: 0;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .modal-content {
                background: white;
                border-radius: 15px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            }
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem;
                border-bottom: 1px solid #e5e7eb;
            }
            .modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #666;
            }
            .modal-body {
                padding: 1.5rem;
            }
            .modal-actions {
                margin-top: 1.5rem;
                display: flex;
                gap: 1rem;
            }
            .btn-primary, .btn-secondary {
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }
            .btn-secondary {
                background: #f3f4f6;
                color: #374151;
            }
            .btn-primary:hover, .btn-secondary:hover {
                transform: translateY(-2px);
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Refresh services status every 30 seconds
setInterval(checkAllServices, 30000);