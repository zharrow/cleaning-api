# 📋 Guide: Créer la migration Alembic

## Étapes pour créer la migration des nouvelles tables

### 1. Vérifier que les modèles sont bien importés

Les modèles suivants doivent être importés dans `api/models/__init__.py` :
- ✅ HACCP models (Child, Supplier, Product, Batch, Meal, Temperature, Equipment, CleaningHaccp, NonCompliance, Document, MealChildren)
- ✅ Communication models (Conversation, Message, Notification)

### 2. Créer la migration automatique

```bash
# Depuis le répertoire cleaning-api
cd cleaning-api

# Option A: Via Docker (recommandé)
docker-compose exec api alembic revision --autogenerate -m "Add HACCP and Communication modules"

# Option B: Via environnement local (si pas Docker)
alembic revision --autogenerate -m "Add HACCP and Communication modules"
```

### 3. Vérifier la migration générée

Le fichier sera créé dans `alembic/versions/` avec un nom comme `xxxxx_add_haccp_and_communication_modules.py`

**Tables qui doivent apparaître** :

**HACCP** :
- `child` (id, enterprise_id, last_name, first_name, birth_date, section, allergies, specific_diet, is_active, created_at, updated_at)
- `supplier` (id, enterprise_id, name, contact_name, phone, email, address, haccp_certified, validation_date, created_at, updated_at)
- `product` (id, enterprise_id, supplier_id, name, category, allergens, stock_unit, current_stock, expiry_date, created_at, updated_at)
- `batch` (id, product_id, batch_code, reception_date, received_quantity, reception_temperature, is_compliant, observations, created_at)
- `meal` (id, enterprise_id, supplier_id, batch_id, responsible_id, date, meal_type, description, created_at, updated_at)
- `temperature` (id, meal_id, responsible_id, checkpoint, temperature, is_compliant, observations, control_date, created_at)
- `equipment` (id, enterprise_id, name, type, last_control_date, target_temperature, is_compliant, observations, created_at, updated_at)
- `cleaning_haccp` (id, enterprise_id, responsible_id, zone, product_used, frequency, cleaning_date, observations, created_at)
- `non_compliance` (id, enterprise_id, responsible_id, type, description, report_date, corrective_action, status, created_at, updated_at)
- `document` (id, enterprise_id, responsible_id, name, category, file_path, creation_date, retention_period, created_at)
- `meal_children` (id, meal_id, child_id, portion, observations, created_at)

**Communication** :
- `conversation` (id, admin_id, developer_id, last_message_at, created_at, updated_at)
- `message` (id, conversation_id, sender_type, sender_id, recipient_type, recipient_id, content, status, created_at, read_at)
- `notification` (id, enterprise_id, recipient_type, recipient_id, title, content, type, priority, status, resource_type, resource_id, created_at, read_at)

**Vérifier les ENUM types** :
- Section (Babies, Toddlers, Preschoolers)
- MealType (Breakfast, Lunch, Snack)
- Checkpoint (Reception, Holding, Service, Storage)
- CleaningFrequency (Daily, Weekly, Monthly)
- NonComplianceType (Product, Temperature, Hygiene, Other)
- NonComplianceStatus (Open, Corrected, Closed)
- DocumentCategory (Temperatures, Cleaning, Training, Compliance, Other)
- SenderType (Developer, Admin)
- RecipientType (Developer, Admin, User)
- MessageStatus (Sent, Delivered, Read)
- NotificationPriority (Info, Warning, Critical)
- NotificationStatus (Unread, Read, Archived)

### 4. Appliquer la migration

```bash
# Option A: Via Docker
docker-compose exec api alembic upgrade head

# Option B: Via environnement local
alembic upgrade head
```

### 5. Vérifier que les tables existent

```bash
# Se connecter à PostgreSQL
docker-compose exec db psql -U postgres -d cleaning_db

# Lister les tables
\dt

# Vérifier une table spécifique
\d child
\d meal
\d conversation
\d notification

# Quitter
\q
```

### 6. En cas d'erreur

Si la migration échoue :

```bash
# Voir le statut
alembic current

# Revenir en arrière
alembic downgrade -1

# Supprimer le fichier de migration généré
rm alembic/versions/xxxxx_add_haccp_and_communication_modules.py

# Recréer la migration
alembic revision --autogenerate -m "Add HACCP and Communication modules"
```

### 7. Test rapide via API

Une fois la migration appliquée, tester avec Swagger:
- Accéder à http://localhost:8000/docs
- Tester un endpoint HACCP (ex: GET /haccp/children)
- Tester un endpoint Communication (ex: GET /communication/notifications)

## Notes importantes

⚠️ **Avant de lancer la migration** :
- Faire un backup de la base : `docker-compose exec db pg_dump -U postgres cleaning_db > backup.sql`
- Vérifier que tous les routers sont bien enregistrés dans `main.py`
- S'assurer que l'environnement Docker est bien lancé : `docker-compose up -d`

✅ **Après la migration** :
- Vérifier les logs : `docker-compose logs api`
- Tester les endpoints dans Swagger
- Créer quelques données de test pour valider
