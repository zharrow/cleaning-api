# Makefile - Commandes utiles
# TODO: Copier le contenu de l'artifact "env_and_config"

.PHONY: install run test lint

install:
	pip install -r requirements.txt

run:
	uvicorn main:app --reload

# TODO: Ajouter toutes les commandes
