FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy necessary files
COPY main.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask app port
EXPOSE 3000

# Run the Flask app
CMD ["python", "main.py"]
