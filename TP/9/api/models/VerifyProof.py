from pydantic import BaseModel, Field, field_validator
import re
import messages as Messages

class VerifyProof(BaseModel):
    proposalId: str = Field(..., description="Hash raíz del árbol de Merkle (0x...)")
    leaf: str = Field(..., description="Hash de la hoja a verificar (0x...)")
    proof: list[str] = Field(..., description="Lista de hashes hermanos en el camino a la raíz")

    @field_validator("proposalId", "leaf")
    @classmethod
    def validate_hashes(cls, value: str) -> str:
        if not value or not isinstance(value, str):
            raise ValueError(Messages.MISSING_FIELD)
        
        # Validar formato de hash de 32 bytes (64 caracteres hexadecimales + 0x)
        if not re.match(r"^0x[0-9a-fA-F]{64}$", value.strip()):
            raise ValueError(Messages.INVALID_PROPOSAL)
            
        return value.strip().lower()

    @field_validator("proof")
    @classmethod
    def validate_proof_list(cls, value: list[str]) -> list[str]:
        if value is None:
            raise ValueError(Messages.MISSING_FIELD)
            
        if len(value) > 7:
            raise ValueError(Messages.PROOF_TOO_LONG)
            
        cleaned_proof = []
        for element in value:
            if not isinstance(element, str) or not re.match(r"^0x[0-9a-fA-F]{64}$", element.strip()):
                raise ValueError(Messages.INVALID_PROPOSAL)
            cleaned_proof.append(element.strip().lower())
            
        return cleaned_proof