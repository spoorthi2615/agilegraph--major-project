FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/src /app/src

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Provide a default entrypoint to the CLI
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
