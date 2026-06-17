#clase Settings para cargar configuraciones
import logging
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    web3_provider_url: str = Field(alias="WEB3_PROVIDER_URL")
    contract_address: str = Field(alias="CFP_FACTORY_ADDRESS")
    mnemonic_phrase: str = Field(alias="CFP_MNEMONIC")
    derivacion_path: str = Field(alias="DERIVACION_PATH")
    db_path: str = Field(alias="CFP_DB_PATH")
    admin_address: str = Field(alias="CFP_ADMIN_ADDRESS")
    upload_dir: str = Field(alias="PROPOSALS_UPLOAD_DIR")

    #carga la configuración desde el archivo .env y permite ignorar campos adicionales no definidos en esta clase
    model_config = SettingsConfigDict(env_file=".env",
                                      extra="ignore",
                                      populate_by_name=True)

@lru_cache
def get_settings() -> Settings:
    return Settings()