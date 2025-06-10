FROM ollama/ollama:latest

# Install Node.js and dependencies
RUN apk add --no-cache nodejs npm

# Set working directory
WORKDIR /app

# Copy dependencies and install
COPY package*.json ./
RUN npm install

# Copy app files
COPY . .

# Environment config
COPY config/anything-llm.env .env

# Entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 3001

CMD ["/entrypoint.sh"]
