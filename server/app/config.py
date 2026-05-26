from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./todo.db"
    
    # Clés API séparées par des virgules dans l'environnement, stockées comme liste
    API_KEYS_RAW: str = "widget-token-secure-789,ai-agent-token-secure-101"
    
    @property
    def api_keys(self) -> List[str]:
        return [key.strip() for key in self.API_KEYS_RAW.split(",") if key.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
