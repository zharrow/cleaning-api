import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.models.user import User
from api.models.session import CleaningSession, CleaningLog
from api.models.export import Export
from api.services.export_service import generate_pdf_report_task, generate_zip_photos_task
import os

router = APIRouter()

@router.post("/pdf/{session_id}")
async def generate_pdf_report(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    background_tasks.add_task(generate_pdf_report_task, session_id)
    return {"message": "Génération du PDF en cours"}

@router.post("/zip/{session_id}")
async def generate_zip_photos(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    background_tasks.add_task(generate_zip_photos_task, session_id)
    return {"message": "Génération du ZIP en cours"}

@router.post("/pdf/{session_id}/download")
async def generate_and_download_pdf(
    session_id: uuid.UUID,
    include_photos: bool = True,
    max_photos: int = 10,
    format_type: str = "standard",  # "standard", "summary", "detailed"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Génère et télécharge immédiatement le PDF d'une session"""
    import tempfile
    import os
    from datetime import datetime

    try:
        # Vérifier que la session existe
        session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")

        # Récupérer les logs de manière simple
        logs = db.query(CleaningLog).filter(
            CleaningLog.session_id == session_id
        ).all()

        print(f"Génération PDF pour session {session_id}, {len(logs)} logs trouvés")

        # Version avancée avec tableaux et design professionnel
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm, inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from collections import defaultdict

            # Créer le fichier PDF temporaire
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file_path = tmp_file.name

            # Créer le document PDF avec marges
            doc = SimpleDocTemplate(tmp_file_path, pagesize=A4,
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)

            # Styles
            styles = getSampleStyleSheet()

            # Style pour le titre principal
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2E5984')
            )

            # Style pour les sous-titres de pièces
            room_title_style = ParagraphStyle(
                'RoomTitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=10,
                spaceBefore=20,
                textColor=colors.HexColor('#1F4E79'),
                leftIndent=0
            )

            # Style pour les statistiques
            stats_style = ParagraphStyle(
                'StatsStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=15,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#495057')
            )

            # Contenu du document
            story = []

            # ========================================
            # PAGE DE COUVERTURE PROFESSIONNELLE
            # ========================================

            # Logo/En-tête entreprise (espace réservé)
            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666'),
                spaceAfter=30
            )

            story.append(Paragraph("cLean - Application de Gestion de Nettoyage", header_style))
            story.append(Spacer(1, 40))

            # Titre principal avec style amélioré
            main_title_style = ParagraphStyle(
                'MainTitle',
                parent=styles['Title'],
                fontSize=28,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1F4E79'),
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph("📋 RAPPORT DE SESSION", main_title_style))
            story.append(Paragraph("DE NETTOYAGE", main_title_style))

            story.append(Spacer(1, 40))

            # Informations de session dans un cadre
            try:
                date_str = session.date.strftime('%A %d %B %Y')
                session_info_style = ParagraphStyle(
                    'SessionInfo',
                    parent=styles['Normal'],
                    fontSize=16,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor('#2E5984'),
                    fontName='Helvetica-Bold',
                    spaceAfter=10
                )
                story.append(Paragraph(f"📅 Session du {date_str}", session_info_style))
            except:
                story.append(Paragraph(f"📅 Session ID: {session_id}", session_info_style))

            # Résumé exécutif sur page de couverture
            total_tasks = len(logs)
            completed_tasks = len([l for l in logs if hasattr(l, 'status') and l.status and str(l.status.value) == 'fait'])
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            summary_style = ParagraphStyle(
                'SummaryStyle',
                parent=styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#495057'),
                spaceAfter=15
            )

            story.append(Spacer(1, 40))
            story.append(Paragraph(f"🎯 Taux de Réussite Global: {completion_rate:.1f}%", summary_style))
            story.append(Paragraph(f"📊 {completed_tasks}/{total_tasks} tâches terminées", summary_style))

            # Informations de génération
            story.append(Spacer(1, 60))
            footer_cover_style = ParagraphStyle(
                'FooterCover',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666')
            )
            story.append(Paragraph(
                f"📄 Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}<br/>"
                f"⚡ Application cLean v1.0",
                footer_cover_style
            ))

            # Saut de page après la couverture
            story.append(PageBreak())

            # ========================================
            # DÉBUT DU CONTENU PRINCIPAL
            # ========================================

            # En-tête du contenu principal
            story.append(Paragraph("📊 STATISTIQUES DÉTAILLÉES", title_style))
            story.append(Spacer(1, 20))

            # Recalculer les statistiques détaillées pour le contenu principal
            partial_tasks = len([l for l in logs if hasattr(l, 'status') and l.status and str(l.status.value) == 'partiel'])
            postponed_tasks = len([l for l in logs if hasattr(l, 'status') and l.status and str(l.status.value) == 'reporte'])
            impossible_tasks = len([l for l in logs if hasattr(l, 'status') and l.status and str(l.status.value) == 'impossible'])

            # Tableau de statistiques globales
            stats_data = [
                ['📊 STATISTIQUES GLOBALES', '', '', '', ''],
                ['Total', 'Terminées ✅', 'Partielles ⚠️', 'Reportées ⏸️', 'Impossibles ❌'],
                [str(total_tasks), str(completed_tasks), str(partial_tasks), str(postponed_tasks), str(impossible_tasks)],
                ['100%', f'{(completed_tasks/total_tasks*100):.1f}%' if total_tasks > 0 else '0%',
                 f'{(partial_tasks/total_tasks*100):.1f}%' if total_tasks > 0 else '0%',
                 f'{(postponed_tasks/total_tasks*100):.1f}%' if total_tasks > 0 else '0%',
                 f'{(impossible_tasks/total_tasks*100):.1f}%' if total_tasks > 0 else '0%']
            ]

            stats_table = Table(stats_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 3*cm])
            stats_table.setStyle(TableStyle([
                # En-tête principal
                ('SPAN', (0, 0), (4, 0)),
                ('BACKGROUND', (0, 0), (4, 0), colors.HexColor('#2E5984')),
                ('TEXTCOLOR', (0, 0), (4, 0), colors.white),
                ('FONTNAME', (0, 0), (4, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (4, 0), 14),
                ('ALIGN', (0, 0), (4, 0), 'CENTER'),

                # En-têtes de colonnes
                ('BACKGROUND', (0, 1), (4, 1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, 1), (4, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (4, 1), 10),
                ('ALIGN', (0, 1), (4, 1), 'CENTER'),

                # Données numériques
                ('FONTNAME', (0, 2), (4, 3), 'Helvetica'),
                ('FONTSIZE', (0, 2), (4, 3), 12),
                ('ALIGN', (0, 2), (4, 3), 'CENTER'),

                # Bordures et espacement
                ('GRID', (0, 0), (4, 3), 1, colors.HexColor('#DDDDDD')),
                ('VALIGN', (0, 0), (4, 3), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 2), (4, 3), [colors.white, colors.HexColor('#F8F9FA')])
            ]))

            story.append(stats_table)
            story.append(Spacer(1, 30))

            # Regrouper les tâches par pièce
            tasks_by_room = defaultdict(list)

            for log in logs:
                try:
                    room_name = "Pièce inconnue"
                    if hasattr(log, 'assigned_task') and log.assigned_task:
                        if hasattr(log.assigned_task, 'room') and log.assigned_task.room:
                            room_name = log.assigned_task.room.name

                    tasks_by_room[room_name].append(log)
                except Exception as e:
                    print(f"Erreur lors du regroupement: {e}")
                    tasks_by_room["Erreur de traitement"].append(log)

            # Créer un tableau pour chaque pièce
            for room_name, room_logs in tasks_by_room.items():
                # Titre de la pièce avec émoji
                room_emoji = "🏠"
                if "salle" in room_name.lower():
                    room_emoji = "🏫"
                elif "cuisine" in room_name.lower():
                    room_emoji = "🍽️"
                elif "toilette" in room_name.lower() or "wc" in room_name.lower():
                    room_emoji = "🚽"
                elif "bureau" in room_name.lower():
                    room_emoji = "💼"
                elif "entrée" in room_name.lower():
                    room_emoji = "🚪"

                story.append(Paragraph(f"{room_emoji} {room_name.upper()}", room_title_style))

                # Données du tableau pour cette pièce
                room_data = [['Tâche', 'Statut', 'Exécutant', 'Heure']]

                for log in room_logs:
                    try:
                        # Nom de la tâche
                        task_name = "Tâche inconnue"
                        if hasattr(log, 'assigned_task') and log.assigned_task:
                            if hasattr(log.assigned_task, 'task_template') and log.assigned_task.task_template:
                                task_name = log.assigned_task.task_template.name

                        # Statut avec émoji
                        status = "❓ Inconnu"
                        if hasattr(log, 'status') and log.status:
                            status_value = str(log.status.value) if hasattr(log.status, 'value') else str(log.status)
                            status_emojis = {
                                'fait': '✅ Terminée',
                                'partiel': '⚠️ Partielle',
                                'reporte': '⏸️ Reportée',
                                'impossible': '❌ Impossible'
                            }
                            status = status_emojis.get(status_value, f"❓ {status_value}")

                        # Exécutant
                        performer = "Non assigné"
                        if hasattr(log, 'performed_by') and log.performed_by:
                            performer = log.performed_by.name if hasattr(log.performed_by, 'name') else str(log.performed_by)

                        # Heure
                        time_str = "-"
                        if hasattr(log, 'performed_at') and log.performed_at:
                            try:
                                time_str = log.performed_at.strftime('%H:%M')
                            except:
                                time_str = str(log.performed_at)[:5]  # Fallback

                        room_data.append([task_name, status, performer, time_str])

                    except Exception as log_error:
                        print(f"Erreur avec log dans {room_name}: {log_error}")
                        room_data.append(["Erreur de traitement", "❓ Erreur", "-", "-"])

                # Créer le tableau pour cette pièce
                room_table = Table(room_data, colWidths=[6*cm, 4*cm, 3*cm, 2*cm])
                room_table.setStyle(TableStyle([
                    # En-tête du tableau
                    ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#1F4E79')),
                    ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
                    ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (3, 0), 11),
                    ('ALIGN', (0, 0), (3, 0), 'CENTER'),

                    # Corps du tableau
                    ('FONTNAME', (0, 1), (3, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (3, -1), 9),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Nom tâche à gauche
                    ('ALIGN', (1, 1), (3, -1), 'CENTER'),    # Autres colonnes centrées

                    # Bordures et espacement
                    ('GRID', (0, 0), (3, -1), 0.5, colors.HexColor('#CCCCCC')),
                    ('VALIGN', (0, 0), (3, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (3, -1), [colors.white, colors.HexColor('#F9F9F9')]),

                    # Espacement interne
                    ('LEFTPADDING', (0, 0), (3, -1), 8),
                    ('RIGHTPADDING', (0, 0), (3, -1), 8),
                    ('TOPPADDING', (0, 0), (3, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (3, -1), 6),
                ]))

                story.append(room_table)
                story.append(Spacer(1, 15))

            # ========================================
            # SECTION PHOTOS
            # ========================================

            # Collecter toutes les photos des logs
            all_photos = []
            for log in logs:
                if hasattr(log, 'photo_urls') and log.photo_urls:
                    room_name = "Pièce inconnue"
                    task_name = "Tâche inconnue"

                    if hasattr(log, 'assigned_task') and log.assigned_task:
                        if hasattr(log.assigned_task, 'room') and log.assigned_task.room:
                            room_name = log.assigned_task.room.name
                        if hasattr(log.assigned_task, 'task_template') and log.assigned_task.task_template:
                            task_name = log.assigned_task.task_template.name

                    # Ajouter chaque photo avec son contexte
                    for photo_url in log.photo_urls:
                        all_photos.append({
                            'url': photo_url,
                            'room': room_name,
                            'task': task_name,
                            'timestamp': log.performed_at if hasattr(log, 'performed_at') and log.performed_at else None
                        })

            # Ajouter section photos si il y en a ET si demandé
            if all_photos and include_photos:
                story.append(Spacer(1, 30))
                story.append(Paragraph("📸 DOCUMENTATION PHOTOS", title_style))
                story.append(Spacer(1, 20))

                from reportlab.platypus import Image as RLImage
                import requests
                import tempfile
                import os

                photos_added = 0
                # Utiliser le paramètre max_photos

                for photo_data in all_photos[:max_photos]:
                    try:
                        # Télécharger l'image depuis Firebase
                        response = requests.get(photo_data['url'], timeout=10)
                        if response.status_code == 200:
                            # Créer un fichier temporaire pour l'image
                            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img_path = tmp_img.name

                            # Titre de la photo
                            photo_title_style = ParagraphStyle(
                                'PhotoTitle',
                                parent=styles['Normal'],
                                fontSize=12,
                                fontName='Helvetica-Bold',
                                textColor=colors.HexColor('#1F4E79'),
                                spaceAfter=5,
                                spaceBefore=15
                            )

                            # Info contextuelle
                            photo_info = f"📍 {photo_data['room']} - {photo_data['task']}"
                            if photo_data['timestamp']:
                                try:
                                    time_str = photo_data['timestamp'].strftime('%H:%M')
                                    photo_info += f" - {time_str}"
                                except:
                                    pass

                            story.append(Paragraph(photo_info, photo_title_style))

                            # Insérer l'image (redimensionnée)
                            try:
                                img = RLImage(tmp_img_path, width=8*cm, height=6*cm)
                                story.append(img)
                                photos_added += 1
                                story.append(Spacer(1, 10))
                            except Exception as img_error:
                                print(f"Erreur insertion image: {img_error}")
                                story.append(Paragraph("❌ Erreur de chargement de l'image", styles['Normal']))

                            # Nettoyer le fichier temporaire
                            try:
                                os.unlink(tmp_img_path)
                            except:
                                pass

                    except Exception as photo_error:
                        print(f"Erreur traitement photo {photo_data['url']}: {photo_error}")
                        continue

                # Message récapitulatif des photos
                if photos_added == 0:
                    story.append(Paragraph("❌ Aucune photo n'a pu être chargée", styles['Normal']))
                elif len(all_photos) > max_photos:
                    story.append(Paragraph(
                        f"📊 {photos_added} photos affichées sur {len(all_photos)} disponibles",
                        styles['Normal']
                    ))
                else:
                    story.append(Paragraph(f"📊 {photos_added} photos incluses", styles['Normal']))

            elif include_photos:
                # Photos demandées mais aucune disponible
                story.append(Spacer(1, 30))
                story.append(Paragraph("📸 DOCUMENTATION PHOTOS", title_style))
                story.append(Spacer(1, 10))
                story.append(Paragraph("ℹ️ Aucune photo n'a été prise lors de cette session", styles['Normal']))

            # Si include_photos=False, on n'ajoute pas du tout la section photos

            # Footer avec informations de génération
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666'),
                spaceBefore=20
            )

            story.append(Paragraph(
                f"📄 Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}<br/>"
                f"⚡ Application cLean - Gestion de Nettoyage Professionnelle",
                footer_style
            ))

            # Construire le PDF
            doc.build(story)

            # Nom de fichier avec date et options
            try:
                date_str = session.date.strftime('%Y-%m-%d')
            except:
                date_str = datetime.now().strftime('%Y-%m-%d')

            # Suffixe selon les options
            suffix = ""
            if not include_photos:
                suffix = "_sans_photos"
            elif format_type != "standard":
                suffix = f"_{format_type}"

            filename = f"rapport_nettoyage_{date_str}{suffix}.pdf"

            # Fonction de nettoyage
            def cleanup():
                try:
                    os.unlink(tmp_file_path)
                except Exception as cleanup_error:
                    print(f"Erreur cleanup: {cleanup_error}")

            return FileResponse(
                path=tmp_file_path,
                filename=filename,
                media_type='application/pdf',
                background=cleanup
            )

        except ImportError as import_error:
            raise HTTPException(status_code=500, detail=f"ReportLab non installé: {str(import_error)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur génération PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}")

@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    export = db.query(Export).filter(Export.id == export_id).first()
    if not export:
        raise HTTPException(status_code=404, detail="Export non trouvé")

    if not os.path.exists(export.file_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    return FileResponse(
        path=export.file_path,
        filename=export.filename,
        media_type='application/octet-stream'
    )
