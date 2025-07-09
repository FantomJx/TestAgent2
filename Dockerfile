FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY .github/scripts/ ./scripts/
COPY .github/pr-agent-21ba8-firebase-adminsdk-fbsvc-95c716d6e2.json ./firebase-key.json

# Set environment variables
ENV PYTHONPATH=/app/scripts
ENV FIREBASE_KEY_PATH=/app/firebase-key.json

# Create a non-root user for security
RUN useradd -m -u 1001 testagent
USER testagent

# Default command
CMD ["python", "scripts/ai_review.py"]
