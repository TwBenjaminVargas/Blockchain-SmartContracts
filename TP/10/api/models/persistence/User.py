from enum import Enum
from sqlmodel import SQLModel, Field as SQLField

class UserState(str, Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    AUTHORIZED = "authorized"
    ARCHIVED = "archived"

class User(SQLModel, table=True):
    __tablename__ = "users"

    address: str = SQLField(primary_key=True, description="Dirección de Ethereum (PK)")
    name: str = SQLField(description="Nombre limpio del solicitante persistido")
    signature: str = SQLField(description="Firma criptográfica registrada")
    
    description: str | None = SQLField(default=None, description="Descripción corta o del usuario creador")
    
    state: UserState = SQLField(
        default=UserState.PENDING,
        description="Estado de registro del solicitante sincronizado con la blockchain"
    )
    nonce: int = SQLField(
        default=1,
        description="Valor numérico único de un solo uso para prevenir ataques de replicación, inicia en 1"
    )