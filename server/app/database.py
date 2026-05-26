from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# Configuration de SQLite pour supporter le multi-threading de FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Crée les tables si elles n'existent pas
    SQLModel.metadata.create_all(engine)

def get_session():
    # Fournit une session de base de données à chaque requête API
    with Session(engine) as session:
        yield session
