from pydantic import BaseModel, Field
from typing import List, Optional, Dict
class VerifyReceipt(BaseModel):
    callId: str
    proposalId: str
    title: str
    description: str
    files: list[str]  # Lista de hashes de los archivos que vienen en el recibo
    proofs: Dict[str, List[str]]  # El diccionario completo con las Merkle Proofs de cada hoja
    
    fileHashesToVerify: Optional[List[str]] = Field(
        default=None, 
        description="Hashes específicos que el usuario desea validar contra el árbol de Merkle"
    )