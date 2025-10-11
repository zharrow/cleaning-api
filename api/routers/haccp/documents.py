"""Documents Router - HACCP Module"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.security import get_current_user
from api.core.auth_dependencies import require_manager
from api.models.user import User
from api.models.enterprise import Enterprise
from api.models.haccp_models import Document
from api.schemas.haccp_schemas import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter()

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)])
async def create_document(doc: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    db_doc = Document(enterprise_id=enterprise.id, **doc.dict())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

@router.get("", response_model=List[DocumentResponse])
async def get_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return db.query(Document).filter(Document.enterprise_id == enterprise.id).order_by(Document.creation_date.desc()).all()

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    doc = db.query(Document).filter(Document.id == doc_id, Document.enterprise_id == enterprise.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.put("/{doc_id}", response_model=DocumentResponse, dependencies=[Depends(require_manager)])
async def update_document(doc_id: str, payload: DocumentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    doc = db.query(Document).filter(Document.id == doc_id, Document.enterprise_id == enterprise.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
async def delete_document(doc_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enterprise = db.query(Enterprise).filter(Enterprise.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    doc = db.query(Document).filter(Document.id == doc_id, Document.enterprise_id == enterprise.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(doc)
    db.commit()
    return None
