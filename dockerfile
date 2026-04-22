FROM python:3.10-slim

# System deps (for reportlab, bs4, markdown)
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy nothing else – code will be mounted via volume
ENV PYTHONUNBUFFERED=1

# Chainlit default port
EXPOSE 8000

CMD ["chainlit", "run", "app.py", "-h", "0.0.0.0", "-p", "8000"]
