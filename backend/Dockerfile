# Backend container for Taboo Measure Maker
# Uses psycopg for PostgreSQL while keeping SQLite fallback available via settings.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies only as needed for scientific libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Default database points to PostgreSQL; override TABOO_DATABASE_URL as needed.
ENV TABOO_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/postgres

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
