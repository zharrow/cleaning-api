# 🏗️ Architecture Modulaire - API Nettoyage

## 📁 Structure du projet

```
app/
├── __init__.py
├── main.py                 # Point d'entrée FastAPI
├── core/                   # Configuration et services core
│   ├── config.py          # Configuration Pydantic Settings
│   ├── database.py        # Configuration SQLAlchemy
│   ├── security.py        # Authentification Firebase
│   └── scheduler.py       # APScheduler
├── models/                 # Modèles SQLAlchemy
│   ├── base.py           # Modèles de base
│   ├── user.py           # Modèle User
│   ├── performer.py      # Modèle Performer
│   ├── room.py           # Modèle Room
│   ├── task.py           # Modèles Task*
│   ├── session.py        # Modèles Session/Log
│   └── export.py         # Modèle Export
├── schemas/               # Schémas Pydantic
│   ├── user.py
│   ├── performer.py
│   ├── room.py
│   ├── task.py
│   ├── session.py
│   └── export.py
├── routers/               # Routes FastAPI
│   ├── users.py
│   ├── performers.py
│   ├── rooms.py
│   ├── tasks.py
│   ├── sessions.py
│   ├── logs.py
│   └── exports.py
├── services/              # Logique métier
│   ├── export_service.py
│   └── session_service.py
├── utils/                 # Utilitaires
│   └── file_utils.py
└── tasks/                 # Tâches background
    └── background_tasks.py
```

## 🚀 Avantages de cette architecture

✅ **Séparation des responsabilités** - Chaque module a un rôle précis
✅ **Facilité de maintenance** - Code organisé et lisible
✅ **Scalabilité** - Facile d'ajouter de nouvelles fonctionnalités
✅ **Testabilité** - Tests unitaires par module
✅ **Réutilisabilité** - Services et utilitaires réutilisables

## 🔧 Comment démarrer

1. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos configurations
   ```

3. **Démarrer l'application**
   ```bash
   # Avec uvicorn directement
   uvicorn app.main:app --reload
   
   # Ou avec le script run.py
   python run.py
   ```

## 📝 Ajout de nouvelles fonctionnalités

### Nouveau modèle
1. Créer `app/models/nouveau_modele.py`
2. Ajouter le modèle dans `app/models/__init__.py`
3. Créer les schémas dans `app/schemas/nouveau_modele.py`
4. Créer le router dans `app/routers/nouveau_modele.py`
5. Inclure le router dans `app/main.py`

### Nouveau service
1. Créer `app/services/nouveau_service.py`
2. Importer dans les routers qui en ont besoin

### Nouvelle route
1. Ajouter dans le router approprié
2. Ou créer un nouveau router si nécessaire

## 🧪 Tests

```bash
pytest tests/
```

## 📚 Documentation API

Une fois l'application démarrée :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
