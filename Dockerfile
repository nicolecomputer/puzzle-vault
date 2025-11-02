FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set timezone environment variable (can be overridden at runtime)
ENV TZ=UTC

# Set data path to the volume mount point
ENV DATA_PATH=/data

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev

# Copy the rest of the application
COPY . .

# Create data directory for volume mount
RUN mkdir -p /data

# Make start script executable
RUN chmod +x scripts/start.sh

# Expose port for the web service
EXPOSE 8000

# Run the start script
ENTRYPOINT ["scripts/start.sh"]
