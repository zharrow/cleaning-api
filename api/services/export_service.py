import uuid
import zipfile
from pathlib import Path
from sqlalchemy.orm import Session
from api.core.database import SessionLocal
from api.core.config import settings
from api.models.session import CleaningSession, CleaningLog
from api.models.export import Export

def generate_pdf_report_task(session_id: uuid.UUID):
    """Génère un rapport PDF pour une session"""
    db = SessionLocal()
    try:
        from weasyprint import HTML
        from jinja2 import Template
        
        session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
        logs = db.query(CleaningLog).filter(CleaningLog.session_id == session_id).all()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport de Nettoyage</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .task { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
                .status { font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de Nettoyage</h1>
                <h2>{{ session.date.strftime('%d %B %Y') }}</h2>
            </div>
            {% for log in logs %}
            <div class="task">
                <h3>{{ log.assigned_task.task_template.name }}</h3>
                <p><strong>Pièce:</strong> {{ log.assigned_task.room.name }}</p>
                <p><strong>Exécutant:</strong> {{ log.performer.name }}</p>
                <p><strong>Statut:</strong> <span class="status">{{ log.status.value }}</span></p>
                {% if log.notes %}
                <p><strong>Notes:</strong> {{ log.notes }}</p>
                {% endif %}
                <p><strong>Heure:</strong> {{ log.timestamp.strftime('%H:%M') }}</p>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(session=session, logs=logs)
        
        date_str = session.date.strftime('%d_%B_%Y')
        filename = f"rapport_nettoyage_{date_str}.pdf"
        file_path = settings.uploads_dir / filename
        
        HTML(string=html_content).write_pdf(file_path)
        
        export = Export(
            session_id=session_id,
            export_type="pdf",
            filename=filename,
            file_path=str(file_path)
        )
        db.add(export)
        db.commit()
        
        print(f"PDF généré: {filename}")
        
    except Exception as e:
        print(f"Erreur génération PDF: {e}")
    finally:
        db.close()

def generate_zip_photos_task(session_id: uuid.UUID):
    """Génère un ZIP avec toutes les photos d'une session"""
    db = SessionLocal()
    try:
        session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == session_id, 
            CleaningLog.photos.isnot(None)
        ).all()
        
        date_str = session.date.strftime('%d_%B_%Y')
        filename = f"photos_{date_str}.zip"
        file_path = settings.uploads_dir / filename
        
        with zipfile.ZipFile(file_path, 'w') as zipf:
            for log in logs:
                if log.photos:
                    for photo in log.photos:
                        photo_path = settings.uploads_dir / photo
                        if photo_path.exists():
                            zipf.write(photo_path, photo)
        
        export = Export(
            session_id=session_id,
            export_type="zip",
            filename=filename,
            file_path=str(file_path)
        )
        db.add(export)
        db.commit()
        
        print(f"ZIP généré: {filename}")
        
    except Exception as e:
        print(f"Erreur génération ZIP: {e}")
    finally:
        db.close()
