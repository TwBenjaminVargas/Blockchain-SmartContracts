from typing import Literal
from sqlmodel import SQLModel, Field as SQLField
from models.UserRegister import UserRegister
from enum import Enum

class UserState(str, Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    AUTHORIZED = "authorized"

# Hereda de UserRegister (para traer campos y validadores) y de SQLModel
class User(UserRegister, SQLModel, table=True):
    __tablename__ = "users"

    # Redefinimos address para indicarle a SQLAlchemy que es la clave primaria de la tabla
    address: str = SQLField(primary_key=True, description="Dirección de Ethereum (PK)")
    
    # Campo adicional exclusivo de la persistencia local solicitado por el negocio
    state: UserState = SQLField(
        default=UserState.PENDING,
        description="Estado de registro del solicitante sincronizado con la blockchain"
    )