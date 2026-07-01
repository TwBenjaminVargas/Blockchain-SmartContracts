from sqlmodel import Field, SQLModel
from typing import Optional

class SyncState(SQLModel, table=True):
    __tablename__ = "sync_state"

    id: int = Field(default=1, primary_key=True, description="ID único para el registro de control")
    last_scanned_block: int = Field(default=0, description="Último número de bloque procesado con éxito")