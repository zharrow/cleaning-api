FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/uploads /app/logs

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exposer le port (Render utilise $PORT)
EXPOSE $PORT

# Commande par défaut avec port dynamique pour Render
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}