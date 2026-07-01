from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel

class CallState(str, Enum):
    PENDING = "PENDING"
    CREATED = "CREATED"

class Call(SQLModel, table=True):
    __tablename__ = "calls"

    callId: str = Field(primary_key=True, description="Hash identificador único del llamado")
    title: str = Field(description="Título limpio y validado")
    description: str = Field(description="Descripción limpia y validada")
    creator: str = Field(nullable=False, description="Dirección Ethereum del creador")
    
    state: CallState = Field(
        default=CallState.PENDING, 
        description="Estado interno del ciclo de vida del llamado"
    )
    
    contractAddress: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Dirección física del contrato inteligente en la red"
    )
    
    closingTime: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Timestamp Unix que determina la fecha y hora límite de cierre de la convocatoria"
    )