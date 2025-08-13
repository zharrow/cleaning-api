
# 🧼 Backend - Application de Nettoyage pour Micro-Crèche

## 🧰 Stack technique
- **Langage** : Python 3.11+
- **Framework** : FastAPI
- **ORM** : SQLAlchemy
- **Migrations** : Alembic
- **Base de données** : PostgreSQL
- **Auth** : Firebase Authentication (JWT)
- **PDF export** : WeasyPrint
- **ZIP export** : Python standard lib (zipfile)

---

## 🗃️ Modèle de données

### Table `users`
- `id`: UUID (PK)
- `firebase_uid`: string (unique) ✅ Identifiant venant de Firebase
- `full_name`: string
- `role`: enum(`gerante`)
- `created_at`, `updated_at`

### Table `performers`
- Liste des exécutants (non connectés)
- Utilisée pour `performed_by` dans `CleaningLog`

### Table `rooms`
- Liste des pièces à nettoyer
- Contient nom, description, ordre d’affichage

### Table `task_templates`
- Modèles de tâche réutilisables (ex: "Désinfecter les poignées")

### Table `assigned_tasks`
- Liens entre une tâche et une pièce spécifique
- Contient fréquence (jours, fois par jour), heure suggérée, exécutant par défaut

### Table `cleaning_sessions`
- Une session par jour générée automatiquement
- Statut (`en_cours`, `complétée`, `incomplète`)

### Table `cleaning_logs`
- Enregistrements réels des tâches réalisées
- Statut : `fait`, `partiel`, `reporté`, `impossible`, etc.
- Avec `performed_by`, `notes`, `photos`, `timestamp`

### Table `exports`
- Traque les rapports PDF et fichiers ZIP générés

---

## 🔐 Authentification avec Firebase

1. Le frontend récupère un JWT Firebase après login
2. Ce JWT est envoyé dans le header `Authorization: Bearer <token>`
3. FastAPI vérifie le token avec `firebase_admin.auth.verify_id_token()`
4. Le `uid` est utilisé pour identifier le `User` dans PostgreSQL

---

## 🖨️ Exports

- WeasyPrint génère un **rapport PDF journalier**
- `zipfile` génère un **ZIP des photos** attachées à une session
- Les fichiers sont nommés de manière lisible :
  - `rapport_nettoyage_03_Juillet_2025.pdf`
  - `photos_03_Juillet_2025.zip`

---

## 🚀 Déploiement CI/CD avec Scaleway

1. Dockerisation du backend
2. Push de l'image sur le **Container Registry Scaleway**
3. Déploiement automatique via GitHub Actions :
   - `docker build`, `docker push`
   - Déclencheur de déploiement via API Scaleway
4. Possibilité de déployer sur une instance ou un service container

---

## 🔁 Mode offline

Pas applicable côté backend, mais le backend supporte les synchronisations différées des `CleaningLogs` depuis le frontend PWA (voir frontend.md)
