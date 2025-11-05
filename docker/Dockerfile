FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create agentos user for security
RUN useradd -m -u 1000 agentos && \
    chown -R agentos:agentos /app

# Create data directory
RUN mkdir -p /home/agentos/.agentos/logs && \
    chown -R agentos:agentos /home/agentos/.agentos

# Switch to non-root user
USER agentos

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (if needed for future web interface)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import agentos; print('OK')" || exit 1

# Default command
ENTRYPOINT ["python", "agentos.py"]
CMD ["--help"]