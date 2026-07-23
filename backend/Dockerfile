FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies needed for compiling certs or pdf parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model for local resume parsing fallback
RUN python -m spacy download en_core_web_sm

# Copy backend application source
COPY . .

# Expose port for FastAPI application
EXPOSE 8000

# Command to run database migrations on start, and then launch Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
