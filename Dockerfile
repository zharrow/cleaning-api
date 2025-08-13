FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfribidi0 \
    libfontconfig1 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libxml2 \
    libxslt1.1 \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le répertoire pour les uploads
RUN mkdir -p /app/uploads

# Exposer le port
EXPOSE 8000

# Variables d'environnement par défaut
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Commande de démarrage - pointer vers api.main:app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]