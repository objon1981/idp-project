#!/bin/sh

# Start Ollama in background
echo "Starting Ollama LLM backend..."
ollama serve &

# Wait a few seconds for Ollama to be ready
sleep 5

# Start Anything-LLM server
echo "Starting Anything-LLM frontend server..."
npm run start
