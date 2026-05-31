from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
from uuid import UUID
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse, RedirectResponse
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
    version="1.1.0",
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

# --- DOCUMENTATION ET REDIRECTIONS ---

@app.get("/", include_in_schema=False)
def redirect_root_to_doc():
    """Redirige les requêtes de la racine vers la page de documentation."""
    return RedirectResponse(url="/doc")

@app.get("/doc", response_class=HTMLResponse, include_in_schema=False)
def get_html_documentation():
    """
    Sert une page HTML interactive et magnifiquement stylisée (Glassmorphism)
    rendant le guide d'intégration pour Agent IA (README_AI_AGENT.md).
    """
    try:
        # Chemin relatif vers la racine du serveur (où se trouve le README)
        readme_path = "README_AI_AGENT.md"
        if not os.path.exists(readme_path):
            # Essayer un autre chemin au cas où
            readme_path = "/app/README_AI_AGENT.md"
            
        if not os.path.exists(readme_path):
            raise FileNotFoundError("README_AI_AGENT.md introuvable.")
            
        with open(readme_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
            
        escaped_content = json.dumps(markdown_content)
        
        html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentation TodoFlow API</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {{
      --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      --glass-bg: rgba(30, 41, 59, 0.75);
      --glass-border: rgba(255, 255, 255, 0.08);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #6366f1;
      --primary-glow: rgba(99, 102, 241, 0.15);
      --accent: #10b981;
    }}
    
    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg-gradient);
      color: var(--text-main);
      margin: 0;
      padding: 0;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }}
    
    .container {{
      width: 100%;
      max-width: 900px;
      margin: 40px 20px;
      background: var(--glass-bg);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--glass-border);
      border-radius: 24px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }}
    
    /* Sleek scrollbar */
    ::-webkit-scrollbar {{
      width: 8px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(15, 23, 42, 0.5);
    }}
    ::-webkit-scrollbar-thumb {{
      background: rgba(99, 102, 241, 0.3);
      border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: rgba(99, 102, 241, 0.5);
    }}

    /* Markdown styling */
    .markdown-body h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      margin-top: 0;
      margin-bottom: 24px;
      background: linear-gradient(135deg, #fff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 16px;
    }}
    
    .markdown-body h2 {{
      font-size: 1.6rem;
      font-weight: 600;
      margin-top: 40px;
      margin-bottom: 16px;
      color: #e2e8f0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      padding-bottom: 8px;
    }}
    
    .markdown-body h3 {{
      font-size: 1.2rem;
      font-weight: 600;
      margin-top: 24px;
      margin-bottom: 12px;
      color: #f1f5f9;
    }}
    
    .markdown-body p {{
      line-height: 1.7;
      color: var(--text-muted);
      margin-bottom: 16px;
    }}
    
    .markdown-body code {{
      font-family: 'Fira Code', monospace;
      font-size: 0.9em;
      background: rgba(15, 23, 42, 0.6);
      padding: 3px 6px;
      border-radius: 6px;
      color: #f43f5e;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    .markdown-body pre {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 16px;
      overflow-x: auto;
      margin-bottom: 24px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    
    .markdown-body pre code {{
      background: none;
      padding: 0;
      color: #38bdf8;
      border: none;
      font-size: 0.92em;
    }}
    
    .markdown-body ul, .markdown-body ol {{
      margin-bottom: 20px;
      padding-left: 24px;
      color: var(--text-muted);
      line-height: 1.7;
    }}
    
    .markdown-body li {{
      margin-bottom: 8px;
    }}
    
    .markdown-body a {{
      color: var(--primary);
      text-decoration: none;
      transition: color 0.2s;
    }}
    
    .markdown-body a:hover {{
      color: #818cf8;
      text-decoration: underline;
    }}
    
    .markdown-body blockquote {{
      border-left: 4px solid var(--primary);
      background: var(--primary-glow);
      margin: 20px 0;
      padding: 16px 20px;
      border-radius: 0 12px 12px 0;
    }}
    
    .markdown-body blockquote p {{
      margin: 0;
      color: #cbd5e1;
      font-style: italic;
    }}
    
    .markdown-body hr {{
      border: 0;
      height: 1px;
      background: rgba(255, 255, 255, 0.1);
      margin: 32px 0;
    }}
    
    /* Premium Header Links */
    .top-links {{
      display: flex;
      justify-content: flex-end;
      gap: 16px;
      margin-bottom: 24px;
    }}
    
    .top-link {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 30px;
      font-size: 0.85rem;
      font-weight: 500;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
    }}
    
    .top-link:hover {{
      background: var(--primary);
      border-color: var(--primary);
      box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="top-links">
      <a href="/docs" class="top-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        Swagger UI (API Interactive)
      </a>
      <a href="/openapi.json" class="top-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        OpenAPI Spec (JSON)
      </a>
    </div>
    <div class="markdown-body" id="content">Chargement de la documentation...</div>
  </div>
  <script>
    const markdownText = {escaped_content};
    document.getElementById('content').innerHTML = marked.parse(markdownText);
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_template, status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erreur</h1><p>Impossible de charger la documentation : {str(e)}</p>",
            status_code=500
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
