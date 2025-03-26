FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    typst \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY utils/ ./utils/

# Create necessary directories
RUN mkdir -p temp/output uploads logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_NAME="openai"

# Expose port
EXPOSE 5000

# Start the application
CMD ["python", "app.py"]