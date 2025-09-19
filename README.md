# 🧼 cLean API

cLean API - API moderne et complète pour la gestion des tâches de nettoyage avec authentification Firebase, exports PDF, et fonctionnalités avancées.

## 🚀 Démarrage rapide

### Avec Docker (Recommandé)

```bash
# 1. Cloner le projet
git clone <repository-url>
cd cleaning-api

# 2. Configurer Firebase
# Télécharger firebase-credentials.json depuis Firebase Console
# Le placer à la racine du projet

# 3. Démarrer tous les services
docker-compose up -d

# 4. L'API est disponible sur http://localhost:8000
```

### Installation manuelle

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 4. Initialiser la base de données
python init_db.py

# 5. Démarrer l'application
uvicorn api.main:app --reload
```

## 🏗️ Architecture

### Stack Technique

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Authentification**: Firebase Authentication
- **Cache**: Redis
- **Exports**: WeasyPrint (PDF) + ZipFile
- **Monitoring**: Prometheus + Grafana
- **Déploiement**: Docker + Docker Compose

### Structure du Projet

```
api/
├── 📁 core/              # Configuration et services core
│   ├── config.py         # Settings Pydantic
│   ├── database.py       # SQLAlchemy setup
│   ├── security.py       # Firebase auth
│   └── scheduler.py      # Tâches programmées
├── 📁 models/            # Modèles SQLAlchemy
│   ├── user.py          # Utilisateurs Firebase
│   ├── performer.py     # Employés/Exécutants
│   ├── room.py          # Pièces de la crèche
│   ├── task.py          # Tâches et assignations
│   └── session.py       # Sessions de nettoyage
├── 📁 routers/           # Endpoints FastAPI
│   ├── auth.py          # Authentification
│   ├── dashboard.py     # Tableau de bord
│   ├── sessions.py      # Sessions de nettoyage
│   └── exports.py       # Rapports PDF/ZIP
├── 📁 schemas/           # Schémas Pydantic
├── 📁 services/          # Logique métier
└── 📁 utils/             # Utilitaires
```

## 🔑 Authentification

### Configuration Firebase

1. Créer un projet Firebase
2. Activer Authentication avec Email/Password
3. Télécharger le fichier de service JSON
4. Le renommer `firebase-credentials.json`

### Utilisation

```python
# Côté client (JavaScript/TypeScript)
import { signInWithEmailAndPassword } from 'firebase/auth';

const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();

// Utiliser le token pour les appels API
const response = await fetch('/api/users/me', {
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});
```

## 📊 Base de Données

### Initialisation sans Alembic

Le projet utilise **init_db.py** pour l'initialisation directe :

```bash
# Créer toutes les tables
python init_db.py

# Réinitialiser complètement la DB
docker-compose down -v
docker-compose up -d db redis
python init_db.py

# Ajouter des données de test
python scripts/seed_data.py
```

### Modèle de données

```mermaid
erDiagram
    User ||--o{ Performer : manages
    Performer ||--o{ CleaningLog : performs
    Room ||--o{ AssignedTask : contains
    TaskTemplate ||--o{ AssignedTask : defines
    AssignedTask ||--o{ CleaningLog : generates
    CleaningSession ||--o{ CleaningLog : contains
    CleaningSession ||--o{ Export : generates
```

## 🧹 Fonctionnalités

### Sessions de Nettoyage

```bash
# Créer la session du jour avec toutes les tâches
POST /sessions/today

# Marquer une tâche comme terminée
POST /logs/{log_id}/complete
{
  "performed_by_id": "uuid",
  "status": "fait",
  "note": "Terminé à 14h30"
}

# Validation rapide avec l'exécutant par défaut
POST /logs/{log_id}/quick-complete
```

### Exports et Rapports

```bash
# Générer un rapport PDF
POST /exports/pdf/{session_id}

# Créer un ZIP des photos
POST /exports/zip/{session_id}

# Télécharger un export
GET /exports/{export_id}/download
```

### Tableau de Bord

```bash
# Données complètes du dashboard
GET /dashboard

# Métriques par période
GET /dashboard/metrics?period=week

# Statistiques d'une session
GET /sessions/{session_id}/statistics
```

## 🐳 Services Docker

### Services Principaux

- **app**: API FastAPI (port 8000)
- **db**: PostgreSQL 15 (port 5432)
- **redis**: Cache Redis (port 6379)
- **adminer**: Interface DB (port 8080)

### Services de Monitoring

- **prometheus**: Métriques (port 9090)
- **grafana**: Dashboards (port 3000)
- **backup**: Backup automatique quotidien

### Commandes Utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f app

# Shell dans le container app
docker-compose exec app /bin/sh

# Backup manuel
docker-compose exec backup pg_dump -h db -U postgres cleaning_db > backup.sql

# Restaurer un backup
docker-compose exec -T db psql -U postgres -d cleaning_db < backup.sql
```

## 🛠️ Développement

### Makefile

```bash
# Voir toutes les commandes disponibles
make help

# Démarrage rapide complet
make quick-start

# Tests et qualité
make test
make lint
make format

# Base de données
make db-create
make db-reset
make db-seed
```

### Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=api --cov-report=html

# Tests en mode watch
ptw
```

### Qualité de Code

```bash
# Formatage automatique
black api/ tests/

# Vérification du style
flake8 api/

# Vérification des types
mypy api/

# Vérification de sécurité
bandit -r api/
```

## 📈 Monitoring

### Métriques Disponibles

- Temps de réponse par endpoint
- Nombre de requêtes par minute
- Erreurs 4xx/5xx
- Utilisation CPU/Mémoire
- Sessions de nettoyage par jour

### Grafana

Accès: http://localhost:3000 (admin/admin)

Dashboards pré-configurés :
- Vue d'ensemble de l'API
- Performance base de données
- Métriques métier (tâches, sessions)

## 🚀 Déploiement

### Staging

```bash
# Déclenchement automatique sur push develop
git push origin develop
```

### Production

```bash
# Déclenchement automatique sur push main
git push origin main
```

### Variables d'Environnement Production

```bash
# Sécurité
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=production
DEBUG=false

# Base de données
DATABASE_URL=postgresql://user:pass@host:5432/db

# Firebase
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# CORS
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## 📋 API Documentation

### Endpoints Principaux

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Connexion Firebase |
| GET | `/auth/me` | Profil utilisateur |
| GET | `/dashboard` | Données tableau de bord |
| POST | `/sessions/today` | Créer session du jour |
| POST | `/logs/{id}/complete` | Valider une tâche |
| POST | `/exports/pdf/{session_id}` | Rapport PDF |

### Documentation Interactive

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://...` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `FIREBASE_CREDENTIALS_PATH` | Chemin Firebase JSON | `./firebase-credentials.json` |
| `SECRET_KEY` | Clé secrète | `change-me` |
| `ENVIRONMENT` | Environnement | `development` |
| `MAX_FILE_SIZE` | Taille max upload | `10485760` (10MB) |

### Fichiers de Configuration

- `.env`: Variables d'environnement
- `docker-compose.yml`: Services Docker
- `nginx/nginx.conf`: Configuration proxy
- `monitoring/prometheus.yml`: Métriques

## 🆘 Dépannage

### Problèmes Courants

**Base de données non accessible**
```bash
# Vérifier que PostgreSQL est démarré
docker-compose ps db

# Recréer le container
docker-compose down
docker-compose up -d db
```

**Firebase non configuré**
```bash
# Vérifier le fichier de credentials
ls -la firebase-credentials.json

# Tester les permissions
python -c "import firebase_admin; print('Firebase OK')"
```

**Uploads ne fonctionnent pas**
```bash
# Vérifier les permissions du dossier
mkdir -p uploads
chmod 755 uploads
```

## 📞 Support

Pour toute question ou problème :

1. Consulter les [Issues GitHub](../../issues)
2. Vérifier les logs : `docker-compose logs -f app`
3. Consulter la documentation API : `/docs`

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.