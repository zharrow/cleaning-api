# 🔧 cLean API - Backend FastAPI

Backend API pour l'application cLean avec support HACCP et Communication temps réel.

## 🚀 Démarrage rapide

### Docker (recommandé)
```bash
make docker-up        # Démarre tous les services
make docker-logs      # Voir les logs
make docker-down      # Arrêter les services
```

→ API: http://localhost:8000
→ Docs: http://localhost:8000/docs
→ Adminer: http://localhost:8080

### Local
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## 📚 Documentation

- **[docs/CREATE_MIGRATION.md](docs/CREATE_MIGRATION.md)** - Guide migration Alembic
- **[docs/IMPLEMENTATION_FINALE.md](docs/IMPLEMENTATION_FINALE.md)** - Résumé implémentation
- **[../CLAUDE.md](../CLAUDE.md)** - Documentation complète projet
- **[../database.md](../database.md)** - Schéma base de données

## 🛠️ Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Auth**: Firebase Admin SDK
- **WebSocket**: FastAPI WebSocket
- **Migrations**: Alembic

## 📦 Modules API

### cLean (Nettoyage)
- `/rooms` - Gestion des pièces
- `/tasks` - Gestion des tâches
- `/users` - Gestion des employés
- `/sessions` - Sessions de nettoyage
- `/uploads` - Upload photos Firebase

### HACCP (11 routers)
- `/haccp/children` - Enfants avec allergies
- `/haccp/suppliers` - Fournisseurs certifiés
- `/haccp/products` - Produits et stocks
- `/haccp/batches` - Traçabilité lots
- `/haccp/meals` - Repas quotidiens
- `/haccp/temperatures` - Contrôles température
- `/haccp/equipment` - Maintenance équipements
- `/haccp/cleaning` - Nettoyage HACCP
- `/haccp/non-compliances` - Incidents
- `/haccp/documents` - Documents conformité
- `/haccp/meal-children` - Association repas-enfants

### Communication (4 routers)
- `/communication/conversations` - Conversations Admin ↔ Dev
- `/communication/messages` - Messages avec statuts
- `/communication/notifications` - Notifications multi-tiers
- `/communication/ws/{userType}/{userId}` - WebSocket temps réel

## 🔒 Sécurité

- Authentification Firebase (Admin/Developer)
- Authentification PIN (User/Employé)
- Isolation par `enterprise_id`
- Validation Pydantic sur tous les endpoints

## 🧪 Tests

```bash
make docker-shell
pytest -v
```

## 📊 Base de données

```bash
# Créer migration
alembic revision --autogenerate -m "description"

# Appliquer migrations
alembic upgrade head

# Reset complet
make db-reset
```

---

**Status**: 100% implémenté
**Version**: 1.0.0
