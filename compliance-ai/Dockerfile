# Multi-stage Dockerfile for Enterprise Compliance AI
# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + Pre-seeded Application
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and backend dependencies
COPY pyproject.toml ./
COPY backend ./backend

# Install Python dependencies
RUN pip install --no-cache-dir -e ./backend

# Copy static frontend build into backend static serving directory
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Copy scripts and env configuration
COPY scripts ./scripts
COPY .env.example .env

# Pre-seed vector database during docker build so container starts instantly
RUN python scripts/seed_corpus.py

# Expose port
EXPOSE 8000

# Start uvicorn instantly on container boot
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
