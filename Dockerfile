FROM python:3.11-slim

# Set environment variables to prevent python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install Tesseract OCR and appropriate language packs
# Using root properly inside the Docker container to succeed at these operations
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

# Install dependencies using uv into the system python environment
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application source code
COPY . .

# Start gunicorn on the port provided by Render
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000}"]
