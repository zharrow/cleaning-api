#!/usr/bin/env python3
"""
Script pour définir un utilisateur comme administrateur
"""
from sqlalchemy.orm import sessionmaker
from api.core.database import engine
from api.models.user import User, UserRole

def set_user_as_admin(firebase_uid: str):
    """Met à jour un utilisateur pour le rendre admin"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        user = session.query(User).filter(User.firebase_uid == firebase_uid).first()
        
        if not user:
            print(f"Aucun utilisateur trouvé avec firebase_uid: {firebase_uid}")
            return False
        
        user.role = UserRole.ADMIN
        session.commit()
        
        print(f"Utilisateur {user.full_name} ({firebase_uid}) est maintenant ADMIN")
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    # Votre Firebase UID
    firebase_uid = "N3XlYVdcTORDFmlNlVBq4bB858o1"
    
    set_user_as_admin(firebase_uid)