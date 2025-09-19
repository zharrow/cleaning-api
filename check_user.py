#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from api.core.database import engine
from api.models.user import User, UserRole

def check_and_set_admin():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        firebase_uid = "N3XlYVdcTORDFmlNlVBq4bB858o1"
        
        user = session.query(User).filter(User.firebase_uid == firebase_uid).first()
        
        if not user:
            print(f"Aucun utilisateur trouve avec firebase_uid: {firebase_uid}")
            return False
        
        print(f"Utilisateur trouve: {user.full_name}")
        print(f"Role actuel: {user.role}")
        
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            session.commit()
            print(f"Role mis a jour vers ADMIN pour {user.full_name}")
        else:
            print("Utilisateur deja ADMIN")
        
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    check_and_set_admin()