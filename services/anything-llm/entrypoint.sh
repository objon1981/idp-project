#!/bin/bash
set -e

# Create logs directory
mkdir -p logs

echo "Starting Ollama LLM backend..."
ollama serve &
OLLAMA_PID=$!

# Wait until Ollama is reachable with timeout
echo "Waiting for Ollama to start..."
TIMEOUT=60
COUNTER=0
until curl -s http://localhost:11434/api/version > /dev/null; do
  sleep 1
  COUNTER=$((COUNTER + 1))
  if [ $COUNTER -gt $TIMEOUT ]; then
    echo "Timeout waiting for Ollama to start"
    exit 1
  fi
done

echo "Ollama is ready. Pulling model if needed..."
ollama pull ${OLLAMA_MODEL:-tinyllama} || echo "Model pull failed, continuing..."

echo "Starting Anything-LLM frontend server..."

# Trap signals and cleanup
trap 'echo "Shutting down..."; kill $OLLAMA_PID; exit 0' SIGTERM SIGINT

npm run start