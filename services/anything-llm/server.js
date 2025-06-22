const express = require("express");
const dotenv = require("dotenv");
const axios = require("axios");
const rateLimit = require("express-rate-limit");
const helmet = require("helmet");
const cors = require("cors");
const winston = require("winston");

dotenv.config();

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'anything-llm' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: "Too many requests, please try again later" }
});
app.use('/ask', limiter);

app.use(express.json({ limit: '10mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.json({
    memory: process.memoryUsage(),
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

app.post("/ask", async (req, res) => {
  const { prompt, model, stream = false, temperature = 0.7 } = req.body;
  
  if (!prompt || typeof prompt !== 'string' || prompt.trim().length === 0) {
    return res.status(400).json({ error: "Valid prompt is required" });
  }

  if (prompt.length > 4000) {
    return res.status(400).json({ error: "Prompt too long. Maximum 4000 characters." });
  }

  const requestId = Math.random().toString(36).substring(7);
  logger.info(`Request ${requestId}: Processing prompt`, { 
    promptLength: prompt.length, 
    model: model || process.env.OLLAMA_MODEL 
  });

  try {
    const response = await axios.post(`${process.env.OLLAMA_HOST}/api/generate`, {
      model: model || process.env.OLLAMA_MODEL || "llama3",
      prompt: prompt.trim(),
      stream,
      options: {
        temperature,
        num_predict: 1000
      }
    }, {
      timeout: 60000, // 60 second timeout
      headers: {
        'Content-Type': 'application/json'
      }
    });

    logger.info(`Request ${requestId}: Successfully generated response`);
    res.json({ 
      answer: response.data.response,
      model: response.data.model,
      requestId
    });
  } catch (err) {
    logger.error(`Request ${requestId}: LLM generation failed`, { 
      error: err.message,
      stack: err.stack,
      prompt: prompt.substring(0, 100) + '...'
    });

    if (err.code === 'ECONNREFUSED') {
      return res.status(503).json({ 
        error: "LLM service unavailable", 
        requestId 
      });
    }

    if (err.response?.status === 404) {
      return res.status(400).json({ 
        error: "Model not found", 
        requestId 
      });
    }

    res.status(500).json({ 
      error: "Internal server error", 
      requestId 
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error', { error: err.message, stack: err.stack });
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

const PORT = process.env.PORT || 3001;

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Process terminated');
    process.exit(0);
  });
});

const server = app.listen(PORT, '0.0.0.0', () => {
  logger.info(`Anything-LLM listening on port ${PORT}`);
});

module.exports = app;