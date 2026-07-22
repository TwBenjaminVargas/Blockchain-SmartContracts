from sqlmodel import SQLModel, Field as SQLField
from typing import Optional
from enum import Enum

class ProposalState(str, Enum):
    CREATED= "created"
    PENDING = "pending"
    DELIVERED = "delivered"

class Proposal(SQLModel, table=True):
    __tablename__ = "proposals"

    proposalId: str = SQLField(primary_key=True, description="Raíz del árbol de Merkle (PK)")
    callId: str = SQLField(foreign_key="calls.callId", index=True, description="Hash del llamado asociado")
    title: str = SQLField(description="Título limpio")
    titleHash: str = SQLField(description="keccak256 del título")
    description: str = SQLField(description="Descripción limpia")
    descriptionHash: str = SQLField(description="keccak256 de la descripción")
    filesJson: str = SQLField(description="Lista de archivos persistidos en formato JSON string")
    proofsJson: str = SQLField(description="Mapa de pruebas de Merkle persistido en JSON string")
    
    created: int = SQLField(description="Timestamp Unix de confirmación on-chain",nullable=True)
    createdBlocknumber: int = SQLField(description="Número de bloque en el que se minó la transacción",nullable=True)
    registrationTransactionHash: str = SQLField(description="Hash único de la transacción en la blockchain",nullable=True)
    sender: str = SQLField(description="Dirección de la cuenta del servidor que envió la TX",nullable=True)
    
    filesDelivered: bool = SQLField(default=False)
    deliveryTransactionHash: Optional[str] = SQLField(default=None, nullable=True)
    deliveryBlockNumber: Optional[int] = SQLField(default=None, nullable=True)
    
    state: ProposalState = SQLField(
        description="Estado de propuesta sincronizada con la blockchain"
    )
    