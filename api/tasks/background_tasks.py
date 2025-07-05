from datetime import date
from api.core.database import SessionLocal
from api.models.session import CleaningSession

async def generate_daily_sessions():
    """Génère automatiquement les sessions de nettoyage quotidiennes"""
    db = SessionLocal()
    try:
        today = date.today()
        
        existing_session = db.query(CleaningSession).filter(
            CleaningSession.date == today
        ).first()
        
        if not existing_session:
            session = CleaningSession(date=today)
            db.add(session)
            db.commit()
            print(f"Session créée pour {today}")
            
    except Exception as e:
        print(f"Erreur lors de la génération de session: {e}")
    finally:
        db.close()
