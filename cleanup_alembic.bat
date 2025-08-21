@echo off
REM Script de nettoyage pour supprimer Alembic du projet (Windows)

echo 🧹 Nettoyage d'Alembic du projet...

REM === SUPPRESSION DES FICHIERS ALEMBIC ===
echo 📁 Suppression des fichiers Alembic...

REM Supprimer le dossier alembic complet
if exist "alembic" (
    rmdir /s /q "alembic"
    echo ✅ Dossier alembic\ supprimé
) else (
    echo ℹ️ Dossier alembic\ n'existe pas
)

REM Supprimer alembic.ini
if exist "alembic.ini" (
    del "alembic.ini"
    echo ✅ Fichier alembic.ini supprimé
) else (
    echo ℹ️ Fichier alembic.ini n'existe pas
)

REM === RECHERCHE DES REFERENCES DANS LE CODE ===
echo 🔍 Recherche des références Alembic dans le code...

REM Utiliser findstr pour chercher les références
findstr /s /i "alembic" *.py *.yml *.yaml *.md *.txt Makefile 2>nul
if errorlevel 1 (
    echo ✅ Aucune référence Alembic trouvée dans les fichiers
) else (
    echo ⚠️ Références Alembic trouvées - Veuillez vérifier manuellement ces fichiers
)

REM === VERIFICATION DES WORKFLOWS GITHUB ===
echo 🔧 Vérification des workflows GitHub Actions...

if exist ".github\workflows" (
    findstr /s /i "alembic" .github\workflows\*.yml 2>nul
    if not errorlevel 1 (
        echo ⚠️ Références Alembic trouvées dans les workflows
        echo    → Remplacer 'alembic upgrade head' par 'python init_db.py'
    )
)

REM === VERIFICATION DU README ===
echo 📚 Vérification de la documentation...

if exist "README.md" (
    findstr /i "alembic" README.md >nul 2>&1
    if not errorlevel 1 (
        echo ⚠️ Références Alembic trouvées dans README.md
        echo    → Mettre à jour les instructions de setup
    )
)

REM === VERIFICATION DU MAKEFILE ===
echo 🔨 Vérification du Makefile...

if exist "Makefile" (
    findstr /i "alembic" Makefile >nul 2>&1
    if not errorlevel 1 (
        echo ⚠️ Références Alembic trouvées dans Makefile
        echo    → Remplacer les commandes alembic par init_db.py
    )
)

REM === VERIFICATION DES DEPENDANCES ===
echo 📦 Vérification des dépendances...

if exist "requirements.txt" (
    findstr /i "alembic" requirements.txt >nul 2>&1
    if not errorlevel 1 (
        echo ⚠️ Alembic trouvé dans requirements.txt
        echo    → Supprimer la ligne 'alembic==...'
    )
)

echo.
echo ✅ Nettoyage d'Alembic terminé !
echo.
echo 📝 Actions manuelles recommandées :
echo 1. Vérifier les fichiers mentionnés ci-dessus
echo 2. Mettre à jour README.md avec les nouvelles instructions
echo 3. Remplacer 'alembic upgrade head' par 'python init_db.py' dans les workflows
echo 4. Tester que init_db.py fonctionne correctement
echo 5. Supprimer la ligne alembic de requirements.txt si présente
echo.
echo 🚀 Le projet utilise maintenant init_db.py pour l'initialisation de la DB

pause