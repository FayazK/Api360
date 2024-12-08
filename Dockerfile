# Use Python slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Note: Combined into single RUN command to reduce layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Required for text extraction
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libreoffice \
    # Required for build dependencies
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    # Required for PDF processing
    weasyprint \
    # Required for audio processing
    ffmpeg \
    # Cleanup apt cache to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/
COPY app/main.py .


# Create necessary directories
RUN mkdir -p /app/temp && \
    chmod 777 /app/temp

RUN mkdir -p /app/static && \
    chmod 777 /app/static

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]