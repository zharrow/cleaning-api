#!/usr/bin/env python3
"""
Script de test pour identifier le problème avec TaskTemplate
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models.task import TaskTemplate
from api.core.database import engine, SessionLocal
from sqlalchemy import text

def test_table_structure():
    """Teste la structure de la table"""
    print("=== Test de la structure de la table ===")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'task_templates' 
            ORDER BY ordinal_position;
        """))
        
        columns = list(result)
        print("Colonnes dans task_templates:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    
    return columns

def test_model_definition():
    """Teste la définition du modèle"""
    print("\n=== Test de la définition du modèle ===")
    
    # Afficher les colonnes du modèle
    print("Colonnes dans le modèle TaskTemplate:")
    for col_name, column in TaskTemplate.__table__.columns.items():
        print(f"  - {col_name}: {column.type}")

def test_task_creation():
    """Teste la création d'une tâche"""
    print("\n=== Test de création d'une tâche ===")
    
    db = SessionLocal()
    try:
        # Essayer de créer une tâche avec name
        task_data = {
            'name': 'Test Task',
            'description': 'Test description',
            'category': 'Test',
            'default_duration': 15,
            'estimated_duration': 15
        }
        
        print(f"Tentative de création avec les données: {task_data}")
        
        task = TaskTemplate(**task_data)
        print("✅ TaskTemplate créé avec succès en mémoire")
        
        db.add(task)
        db.commit()
        print("✅ TaskTemplate sauvegardé en base avec succès")
        
        # Vérifier qu'on peut le récupérer
        retrieved = db.query(TaskTemplate).filter_by(name='Test Task').first()
        if retrieved:
            print(f"✅ Tâche récupérée: {retrieved.name}")
        
        # Nettoyer
        db.delete(retrieved)
        db.commit()
        print("✅ Tâche de test supprimée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        print(f"Type d'erreur: {type(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    try:
        test_table_structure()
        test_model_definition()
        test_task_creation()
    except Exception as e:
        print(f"Erreur globale: {e}")
        import traceback
        traceback.print_exc()