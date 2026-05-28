from models.CallCreate import CallCreate
from sqlmodel import Field, SQLModel

class Call(CallCreate,SQLModel, table=True):
    __tablename__ = "calls"

    callId: str = Field(primary_key=True)
    
    creator: str = Field(
        nullable=False, 
        description="Dirección Ethereum del creador autorizado, recuperada de la firma"
    )
    state: str = Field(
        default="PENDING", 
        description="Estado interno del ciclo de vida del llamado"
    )