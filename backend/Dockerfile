FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (often required for PostgreSQL drivers like psycopg2)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend codebase (app, model, scripts)
COPY . .

EXPOSE 8080

# IMPORTANT: Bind to 0.0.0.0 and honor Cloud Run's PORT environment variable.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
