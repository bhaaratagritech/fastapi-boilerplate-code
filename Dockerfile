##############################################
# Dockerfile for FastAPI application
# -------------------------------------------
# - Uses Python 3.14 slim image
# - Installs system dependencies required by cryptography libraries
# - Installs project dependencies from pyproject.toml
# - Copies the application source code into /app
# - Starts the FastAPI app via uvicorn
##############################################

FROM python:3.14-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install OS packages required for building cryptography and other deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency metadata first to leverage Docker layer caching
COPY pyproject.toml README.md ./

# Install project dependencies
RUN pip install --upgrade pip && \
    pip install .

# Copy the application source code
COPY app ./app

# Expose FastAPI port
EXPOSE 8000

# Default command: start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

