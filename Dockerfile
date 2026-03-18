# =============================================================================
# Dr. Ikechukwu PA - Flask Application Docker Image
# =============================================================================
# Multi-stage build for production-ready deployment
# 
# Build: docker build -t dr_ikechukwu_pa:latest .
# Run:   docker run -p 5000:5000 --env-file .env dr_ikechukwu_pa:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY src/api/templates/ ./src/api/templates/
COPY src/api/static/ ./src/api/static/

# Create workspace directory for filesystem MCP
RUN mkdir -p /app/project_workspace

# Create non-root user
RUN groupadd -r dr_ikechukwu && useradd -r -g dr_ikechukwu dr_ikechukwu
RUN chown -R dr_ikechukwu:dr_ikechukwu /app
USER dr_ikechukwu

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.api.main
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "src.api.main:app"]

# -----------------------------------------------------------------------------
# Stage 3: Development (alternative target)
# -----------------------------------------------------------------------------
FROM python:3.11-slim as development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p project_workspace

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.api.main
ENV FLASK_ENV=development
ENV DEBUG=True

# Expose port
EXPOSE 5000

# Run development server
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
