FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy GitHub workflows and scripts
COPY .github/ ./.github/

# Install Python dependencies
RUN pip install --no-cache-dir \
    firebase-admin \
    anthropic \
    openai

# Create entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV GITHUB_WORKSPACE=/app

# Expose port (optional, for health checks)
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["--help"]
