from datetime import date
from sqlalchemy.orm import Session
from app.models.session import CleaningSession

def get_or_create_today_session(db: Session) -> CleaningSession:
    """Récupère ou crée la session du jour"""
    today = date.today()
    session = db.query(CleaningSession).filter(CleaningSession.date == today).first()
    
    if not session:
        session = CleaningSession(date=today)
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session
