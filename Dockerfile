FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt .

# Create venv and install dependencies with uv
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Create vectors directory
RUN mkdir -p /app/vectors

# Add venv Python to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose API port
EXPOSE 8769

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8769/health || exit 1

# Run API using venv Python
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8769"]
