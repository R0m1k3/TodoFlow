from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session, select

from app.config import settings
from app.database import create_db_and_tables, get_session
from app.models import Task, TaskCreate, TaskUpdate, TaskResponse, TaskStatus

# Définition du header attendu pour la clé API
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Dépendance pour vérifier la clé API
def verify_api_key(api_key: str = Depends(api_key_header)):
    # L'en-tête est obligatoire pour sécuriser l'API des accès non autorisés
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La clé API est manquante dans l'en-tête X-API-Key."
        )
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide ou non autorisée."
        )
    return api_key

# Cycle de vie de l'application (Lifespan modern FastAPI)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création des tables à l'initialisation du serveur
    create_db_and_tables()
    yield

app = FastAPI(
    title="TodoFlow API",
    description="API centralisée pour la Todo list, connectée au widget de bureau et pilotable par Agent IA.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour permettre au widget (Tauri) de requêter le serveur librement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tauri utilise des protocoles personnalisés ou localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS API ---

@app.get(
    "/api/v1/tasks",
    response_model=List[TaskResponse],
    dependencies=[Depends(verify_api_key)],
    summary="Récupérer toutes les tâches"
)
def read_tasks(
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_session)
):
    """
    Récupère la liste de toutes les tâches stockées.
    Permet de filtrer optionnellement par statut (A faire, En cours, Termine).
    """
    try:
        statement = select(Task)
        if status:
            statement = statement.where(Task.status == status)
        
        # Tri automatique : d'abord les tâches "En cours", puis "À faire", et enfin les "Terminé".
        # En second critère, on trie par date de création décroissante.
        tasks = db.exec(statement).all()
        
        # Tri personnalisé côté serveur pour optimiser l'affichage du widget
        status_priority = {TaskStatus.IN_PROGRESS: 0, TaskStatus.TODO: 1, TaskStatus.DONE: 2}
        tasks.sort(key=lambda t: (status_priority.get(t.status, 9), t.created_at), reverse=False)
        
        return tasks
    except Exception as e:
        # Journaliser et renvoyer une erreur interne propre
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des tâches : {str(e)}"
        )

@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=TaskResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Récupérer les détails d'une tâche"
)
def read_task(task_id: UUID, db: Session = Depends(get_session)):
    """
    Récupère une tâche spécifique par son UUID.
    Renvoie une erreur 404 si la tâche n'existe pas.
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche introuvable."
        )
    return task

@app.post(
    "/api/v1/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
    summary="Créer une nouvelle tâche"
)
def create_task(task_create: TaskCreate, db: Session = Depends(get_session)):
    """
    Crée une nouvelle tâche avec une date de création automatique et un UUID unique.
    """
    try:
        new_task = Task.model_validate(task_create)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de créer la tâche : {str(e)}"
        )

@app.put(
    "/api/v1/tasks/{task_id}",
    response_model=TaskResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Mettre à jour une tâche existante"
)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_session)
):
    """
    Met à jour partiellement ou totalement une tâche.
    Met automatiquement à jour le champ updated_at.
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche introuvable pour mise à jour."
        )
    
    try:
        # Extraction des champs soumis pour une mise à jour partielle
        update_data = task_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        
        # Mise à jour systématique de l'horodatage de modification
        task.updated_at = datetime.utcnow()
        
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la mise à jour de la tâche : {str(e)}"
        )

@app.delete(
    "/api/v1/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key)],
    summary="Supprimer une tâche"
)
def delete_task(task_id: UUID, db: Session = Depends(get_session)):
    """
    Supprime définitivement une tâche par son UUID.
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche introuvable pour suppression."
        )
    try:
        db.delete(task)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la tâche : {str(e)}"
        )
