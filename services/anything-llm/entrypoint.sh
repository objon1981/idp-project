#!/bin/sh

echo "Starting Ollama LLM backend..."
ollama serve &

# Wait until Ollama is reachable
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434 > /dev/null; do
  sleep 1
done

echo "Starting Anything-LLM frontend server..."
npm run start
