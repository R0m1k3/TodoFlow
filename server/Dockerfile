# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Création d'un environnement virtuel propre
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Minimal Image ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Copie de l'environnement virtuel depuis builder
COPY --from=builder /opt/venv /opt/venv
COPY . /app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Création d'un répertoire pour la base de données SQLite persistante
RUN mkdir -p /app/data

# Création d'un utilisateur système non-privilégié pour des raisons de sécurité
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Lancement d'Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

