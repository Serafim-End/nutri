# Telegram Bot Dockerfile
# Supports both polling (dev) and webhook (prod) modes
# Exposes HTTP on port 8081 in webhook mode (Cloudflare provides HTTPS externally)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' botuser && \
    chown -R botuser:botuser /app

USER botuser

# Environment variables (can be overridden at runtime)
# TELEGRAM_MODE: polling (dev) or webhook (prod)
ENV TELEGRAM_MODE=polling
ENV WEBHOOK_PORT=8081
ENV WEBHOOK_HOST=0.0.0.0
ENV WEBHOOK_PATH=/webhook

# Expose port 8081 for webhook mode
EXPOSE 8081

# Health check - works in webhook mode only
# In polling mode, the bot runs without HTTP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD if [ "$TELEGRAM_MODE" = "webhook" ]; then curl -f http://localhost:${WEBHOOK_PORT}/health || exit 1; else exit 0; fi

# Run the bot
CMD ["python", "bot.py"]
