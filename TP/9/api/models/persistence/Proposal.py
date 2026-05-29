from sqlmodel import SQLModel, Field as SQLField
from typing import Optional

class Proposal(SQLModel, table=True):
    __tablename__ = "proposals"

    # Se define proposalId como la Clave Primaria única
    proposalId: str = SQLField(primary_key=True, description="Raíz del árbol de Merkle (PK)")
    
    # Clave foránea vinculada directamente a la tabla 'calls'
    callId: str = SQLField(foreign_key="calls.callId", index=True, description="Hash del llamado asociado")
    
    title: str = SQLField(description="Título limpio")
    titleHash: str = SQLField(description="keccak256 del título")
    description: str = SQLField(description="Descripción limpia")
    descriptionHash: str = SQLField(description="keccak256 de la descripción")
    filesJson: str = SQLField(description="Lista de archivos persistidos en formato JSON string")
    proofsJson: str = SQLField(description="Mapa de pruebas de Merkle persistido en JSON string")