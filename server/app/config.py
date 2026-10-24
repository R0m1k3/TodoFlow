import logging
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anciennes clés par défaut, publiées dans le dépôt : toujours refusées
PUBLIC_DEFAULT_API_KEYS = {"widget-token-secure-789", "ai-agent-token-secure-101"}

log = logging.getLogger("todoflow")


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./todo.db"

    # Clés API séparées par des virgules dans l'environnement, stockées comme liste.
    # Aucune clé par défaut : sans API_KEYS_RAW, l'entrypoint Docker en génère
    # et les conserve dans le volume de données.
    API_KEYS_RAW: str = ""

    @property
    def api_keys(self) -> List[str]:
        keys = [key.strip() for key in self.API_KEYS_RAW.split(",") if key.strip()]
        rejected = [key for key in keys if key in PUBLIC_DEFAULT_API_KEYS]
        if rejected:
            log.warning("Clé(s) API publique(s) par défaut ignorée(s) : définissez API_KEYS_RAW.")
        return [key for key in keys if key not in PUBLIC_DEFAULT_API_KEYS]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
