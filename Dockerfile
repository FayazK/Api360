# Use Ubuntu as base image for better package support
FROM ubuntu:22.04

# Prevent timezone prompt during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    # PDF dependencies
    poppler-utils \
    # Document conversion dependencies
    libreoffice \
    # Image processing dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    # Other dependencies
    antiword \
    unrtf \
    pstotext \
    # Development dependencies
    build-essential \
    libpulse-dev \
    default-jre \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for temporary files
RUN mkdir -p /app/temp

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]