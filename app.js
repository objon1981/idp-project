// Service status checking functionality
const services = [
    { id: 'ocr', name: 'OCR Service', port: 8080, endpoint: '/health' },
    { id: 'docetl', name: 'DocETL', port: 5001, endpoint: '/health' },
    { id: 'file-organizer', name: 'File Organizer', port: 4000, endpoint: '/health' },
    { id: 'anything-llm', name: 'AnythingLLM', port: 3001, endpoint: '/health' },
    { id: 'json-crack', name: 'JSON Crack', port: 3000, endpoint: '/health' },
    { id: 'local-send', name: 'LocalSend', port: 5050, endpoint: '/health' },
    { id: 'pake', name: 'Pake', port: 8081, endpoint: '/health' },
    { id: 'kestra', name: 'Kestra', port: 8082, endpoint: '/health' },
    { id: 'windmill', name: 'Windmill', port: 7780, endpoint: '/health' }
];

async function checkServiceHealth(service) {
    try {
        const response = await fetch(`http://localhost:${service.port}${service.endpoint}`, {
            method: 'GET',
            timeout: 5000
        });
        return response.ok;
    } catch (error) {
        console.log(`Service ${service.name} is not responding:`, error.message);
        return false;
    }
}

function updateServiceStatus(serviceId, isOnline) {
    const statusDot = document.querySelector(`[data-service="${serviceId}"] .status-dot`);
    const statusText = document.querySelector(`[data-service="${serviceId}"] .status-text`);

    if (statusDot && statusText) {
        statusDot.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
        statusText.textContent = isOnline ? 'Online' : 'Offline';
    }
}

async function checkAllServices() {
    console.log('Checking service status...');

    for (const service of services) {
        const isOnline = await checkServiceHealth(service);
        updateServiceStatus(service.id, isOnline);
    }
}

function testService(serviceId) {
    const service = services.find(s => s.id === serviceId);
    if (service) {
        window.open(`http://localhost:${service.port}`, '_blank');
    } else {
        console.error(`Service ${serviceId} not found`);
    }
}

// Chat functionality
function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    if (!chatInput || !chatMessages) return;

    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user';
    userMessage.textContent = message;
    chatMessages.appendChild(userMessage);

    // Clear input
    chatInput.value = '';

    // Simulate AI response
    setTimeout(() => {
        const aiMessage = document.createElement('div');
        aiMessage.className = 'message ai';
        aiMessage.textContent = 'This is a demo response. The AI service will process your document-related queries.';
        chatMessages.appendChild(aiMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 1000);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, initializing services...');

    // Add data attributes to service cards if they don't exist
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach((card, index) => {
        if (index < services.length) {
            card.setAttribute('data-service', services[index].id);
        }
    });

    // Check services immediately and then every 30 seconds
    checkAllServices();
    setInterval(checkAllServices, 30000);

    // Setup chat input handler
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

// Make testService globally available
window.testService = testService;
window.sendMessage = sendMessage;