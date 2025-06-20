
const express = require('express');
const app = express();
const port = 3001;

app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'AnythingLLM', port: 3001 });
});

app.get('/', (req, res) => {
    res.json({
        service: 'AnythingLLM',
        status: 'running',
        endpoints: ['/health', '/chat', '/embeddings'],
        description: 'LLM Integration Service'
    });
});

app.post('/chat', (req, res) => {
    res.json({
        status: 'success',
        message: 'LLM chat would happen here',
        response: 'This is a sample LLM response'
    });
});

app.post('/embeddings', (req, res) => {
    res.json({
        status: 'success',
        embeddings: [0.1, 0.2, 0.3, 0.4, 0.5],
        dimension: 5
    });
});

app.listen(port, '0.0.0.0', () => {
    console.log(`🤖 AnythingLLM Service running on port ${port}`);
});
