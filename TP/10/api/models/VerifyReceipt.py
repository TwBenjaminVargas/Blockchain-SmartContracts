from pydantic import BaseModel
from typing import list

class VerifyReceipt(BaseModel):
    callId: str
    proposalId: str
    title: str
    description: str
    files: list[str]  # Lista de hashes de los archivos que vienen en el recibo