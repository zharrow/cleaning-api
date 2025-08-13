.PHONY: help install dev test lint format clean docker-up docker-down backup restore migrate docs

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := cleaning-api
DOCKER_COMPOSE := docker-compose

# Couleurs pour output
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

install-dev: ## Installe les dépendances de développement
	$(PIP) install -r requirements.txt
	pre-commit install
	@echo "$(GREEN)✅ Environnement de développement configuré$(NC)"

dev: ## Lance le serveur en mode développement
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Lance les tests
	pytest -v --cov=api --cov-report=html --cov-report=term

test-watch: ## Lance les tests en mode watch
	ptw -- -v

lint: ## Vérifie le code avec flake8
	flake8 api/ tests/

format: ## Formate le code avec black
	black api/ tests/

type-check: ## Vérifie les types avec mypy
	mypy api/

security-check: ## Vérifie les vulnérabilités
	pip-audit
	bandit -r api/

clean: ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf logs/*.log

# Docker
docker-up: ## Démarre les services Docker
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Services démarrés$(NC)"
	@echo "API: http://localhost:8000"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

docker-down: ## Arrête les services Docker
	$(DOCKER_COMPOSE) down

docker-build: ## Reconstruit les images Docker
	$(DOCKER_COMPOSE) build --no-cache

docker-logs: ## Affiche les logs Docker
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Ouvre un shell dans le container app
	$(DOCKER_COMPOSE) exec app /bin/sh

# Base de données
db-create: ## Crée la base de données
	$(PYTHON) -c "from api.core.database import engine, Base; Base.metadata.create_all(bind=engine)"

db-drop: ## Supprime toutes les tables
	$(PYTHON) -c "from api.core.database import engine, Base; Base.metadata.drop_all(bind=engine)"

db-seed: ## Remplit la base avec des données de test
	$(PYTHON) scripts/seed_data.py

migrate: ## Crée une nouvelle migration
	alembic revision --autogenerate -m "$(msg)"

migrate-up: ## Applique les migrations
	alembic upgrade head

migrate-down: ## Annule la dernière migration
	alembic downgrade -1

migrate-history: ## Affiche l'historique des migrations
	alembic history

# Backup & Restore
backup: ## Créé un backup de la base de données
	@mkdir -p backups
	@docker exec -t cleaning-backend-db-1 pg_dumpall -c -U postgres > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup créé$(NC)"

restore: ## Restaure la base de données depuis un backup
	@test -n "$(file)" || (echo "$(RED)❌ Usage: make restore file=backups/backup_XXXXXX.sql$(NC)" && exit 1)
	@docker exec -i cleaning-backend-db-1 psql -U postgres < $(file)
	@echo "$(GREEN)✅ Base de données restaurée$(NC)"

# Documentation
docs: ## Génère la documentation
	mkdocs build

docs-serve: ## Lance le serveur de documentation
	mkdocs serve

# Monitoring
logs: ## Affiche les logs de l'application
	tail -f logs/app.log | jq '.'

# Performance
profile: ## Profile l'application
	$(PYTHON) -m cProfile -o profile.stats api/main.py

analyze-profile: ## Analyse le profil
	$(PYTHON) -m pstats profile.stats

# Sécurité
generate-secret: ## Génère une clé secrète
	@$(PYTHON) -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(64)}')"

# Déploiement
deploy-staging: ## Déploie en staging
	git push origin develop

deploy-production: ## Déploie en production
	git push origin main

# Utils
shell: ## Ouvre un shell Python avec le contexte de l'app
	$(PYTHON) -i -c "from api.main import app; from api.core.database import SessionLocal, engine; from api.models import *; db = SessionLocal()"

urls: ## Liste toutes les routes de l'API
	$(PYTHON) scripts/list_routes.py