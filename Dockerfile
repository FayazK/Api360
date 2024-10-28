# Use Ubuntu as base image for better package support
FROM ubuntu:22.04

# Set environment to prevent timezone prompt during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, textract, and other required dependencies in a single step
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    # textract dependencies
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf \
    poppler-utils \
    pstotext \
    tesseract-ocr \
    tesseract-ocr-eng \
    flac \
    ffmpeg \
    lame \
    libmad0 \
    libpulse-dev \
    # PDF and document conversion dependencies
    libreoffice \
    swig \
    build-essential \
    default-jre && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies, including textract
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a directory for temporary files
RUN mkdir /app/temp

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]