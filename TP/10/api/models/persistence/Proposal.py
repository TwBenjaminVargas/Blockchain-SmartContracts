from sqlmodel import SQLModel, Field as SQLField
from typing import Optional

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
    
    created: int = SQLField(description="Timestamp Unix de confirmación on-chain")
    blocknumber: int = SQLField(description="Número de bloque en el que se minó la transacción")
    transactionHash: str = SQLField(description="Hash único de la transacción en la blockchain", index=True)
    sender: str = SQLField(description="Dirección de la cuenta del servidor que envió la TX")
    