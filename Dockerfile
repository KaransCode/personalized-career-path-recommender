# --- Stage 1: install Python deps + spaCy model (cached separately from app code) ---
FROM python:3.11-slim AS deps

WORKDIR /app

# System deps needed to build some Python packages (e.g. scikit-learn wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# --- Stage 2: application image ---
FROM python:3.11-slim

WORKDIR /app

# Reuse installed site-packages from the deps stage instead of reinstalling
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY . .

ENV FLASK_PORT=5000
EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python", "api/app.py"]
