# AegisVision - Multi-Arch Container for AWS Graviton (ARM64) and x86_64
FROM python:3.11-slim

# System dependencies for OpenCV and multimedia processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin dependencies for reproducibility
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs

# Set environment defaults
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    AWS_DEFAULT_REGION=us-east-1

EXPOSE 8000

# Launch AegisVision Server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
