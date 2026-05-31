from pydantic import BaseModel, Field, field_validator
import re
from exceptions.ValidationExceptions import (
    MissingFieldException, 
    InvalidProposalException, 
    ProofTooLongException
)

class VerifyProof(BaseModel):
    proposalId: str = Field(..., description="Hash raíz del árbol de Merkle (0x...)")
    leaf: str = Field(..., description="Hash de la hoja a verificar (0x...)")
    proof: list[str] = Field(..., description="Lista de hashes hermanos en el camino a la raíz")

    @field_validator("proposalId", "leaf")
    @classmethod
    def validate_hashes(cls, value: str) -> str:
        # Si no viene el campo o no es una cadena de texto
        if not value or not isinstance(value, str):
            raise MissingFieldException()
        
        # Validar el formato del hash de 32 bytes (64 caracteres hexadecimales)
        if not re.match(r"^0x[0-9a-fA-F]{64}$", value.strip()):
            raise InvalidProposalException()
            
        return value.strip().lower()

    @field_validator("proof")
    @classmethod
    def validate_proof_list(cls, value: list[str]) -> list[str]:
        if value is None:
            raise MissingFieldException()
            
        # El árbol Merkle soporta hasta 128 hojas, por ende la prueba tiene un tope de altura de 7
        if len(value) > 7:
            raise ProofTooLongException()
            
        cleaned_proof = []
        for element in value:
            # Validar que cada hash hermano dentro de la lista sea un string de 32 bytes válido
            if not isinstance(element, str) or not re.match(r"^0x[0-9a-fA-F]{64}$", element.strip()):
                raise InvalidProposalException()
            cleaned_proof.append(element.strip().lower())
            
        return cleaned_proof