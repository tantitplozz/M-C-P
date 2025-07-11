# GOD-TIER AUTOBUY STACK - Production Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    gnupg \
    software-properties-common &&
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip &&
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Browser automation stage
FROM python:3.11-slim as browser-stage

# Install browser dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    firefox-esr \
    wget \
    curl \
    xvfb \
    x11vnc \
    fluxbox &&
    rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright==1.40.0 &&
    playwright install chromium firefox webkit &&
    playwright install-deps

# Stage 3: Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    firefox-esr \
    xvfb \
    x11vnc \
    fluxbox \
    supervisor \
    nginx \
    redis-server \
    sqlite3 &&
    rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy browser dependencies
COPY --from=browser-stage /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config &&
    chown -R appuser:appuser /app

# Copy configuration files
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV API_HOST=0.0.0.0
ENV API_PORT=8080

# Expose ports
EXPOSE 8080 3000 9090 5900

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to app user
USER appuser

# Start the application
CMD ["/app/startup.sh"]
