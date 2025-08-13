
# 📱 Frontend PWA - Application de Nettoyage pour Micro-Crèche

## 🧰 Stack technique
- **Framework** : Angular 17
- **PWA** : via `@angular/pwa` + Angular Service Worker
- **State management** : RxJS (ou Signals)
- **Offline storage** : IndexedDB (via `ngx-indexed-db` ou `localForage`)
- **Auth** : Firebase Authentication (email/password)

---

## 🔐 Authentification avec Firebase

- Utilisation de `@angular/fire/auth`
- Connexion via email/password
- Récupération du JWT Firebase
- Envoi du token dans `Authorization: Bearer <token>` pour chaque appel API

---

## 🔄 Mode offline (vrai PWA)

- Les tâches du jour (`AssignedTask`) sont pré-cachées au démarrage
- Les validations (`CleaningLog`) sont **enregistrées localement en IndexedDB**
- Une synchronisation automatique est lancée dès que la connexion est rétablie
- Les erreurs ou conflits sont gérés par une file d’attente silencieuse
- Un `SwUpdate` permet de gérer les mises à jour de l’app installée

---

## 📁 Exemple de configuration `ngsw-config.json`

```json
{
  "dataGroups": [
    {
      "name": "api-tasks",
      "urls": ["/api/tasks/**"],
      "cacheConfig": {
        "maxSize": 100,
        "maxAge": "6h",
        "strategy": "freshness"
      }
    }
  ]
}
```

---

## 📋 Pages à créer dans Angular

1. **Page de connexion**
2. **Page d’accueil / Checklist du jour**
   - Par pièce > Par tâche
   - Statut de chaque tâche
3. **Modal / Formulaire validation tâche**
   - Performer
   - Heure
   - Photo / commentaire
4. **Historique des sessions**
5. **Vue session passée**
6. **Admin (Rooms / Tasks / Performers / Paramètres)**

---

## 📦 Fonctionnalités spécifiques
- Affichage clair par pièce > tâche
- Pastilles de statut couleur
- Photo et commentaire facultatif
- Tâche liée à un performer (non authentifié)

---

## 🧾 Synchronisation

- Les `CleaningLogs` sont envoyés au backend dès que la connexion revient
- Si la session est complète → l'app déclenche le téléchargement + impression du PDF

---

## 🔐 Sécurité
- Seule la gérante se connecte
- Les autres exécutants (`Performer`) sont choisis dans une liste ou saisis
- Chaque log enregistre qui l’a saisi (`user_id`) et qui a exécuté (`performed_by`)
