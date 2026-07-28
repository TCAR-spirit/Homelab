FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code. The source folder IS the `zordon` package, so copy it into a
# `zordon/` subdir under /app. This makes `python -m zordon.main` resolve the
# relative imports (`from . import config`) correctly.
COPY . /app/zordon/
WORKDIR /app

# lore log persists via mounted volume at /app/data
RUN mkdir -p /app/data

CMD ["python", "-m", "zordon.main"]
