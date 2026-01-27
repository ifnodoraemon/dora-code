FROM python:3.11-slim

LABEL org.opencontainers.image.source=https://github.com/doraemon-code/doraemon
LABEL org.opencontainers.image.description="Doraemon Code - AI Assistant powered by MCP"
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application code
COPY src/ ./src/

# Create directory for doraemon data
RUN mkdir -p /root/.doraemon

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Entry point
ENTRYPOINT ["dora"]
CMD ["start"]
