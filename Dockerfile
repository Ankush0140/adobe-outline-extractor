# Multi-stage build for optimization
FROM --platform=linux/amd64 python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (keep under 200MB for Round 1A)
RUN python -m spacy download en_core_web_sm

# Production stage
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false

# Set permissions
RUN chmod +x /app/scripts/setup.sh || true

# Default command for Round 1A
CMD ["python", "round1a/main.py"]

# For Round 1B, use: CMD ["python", "round1b/main.py"]