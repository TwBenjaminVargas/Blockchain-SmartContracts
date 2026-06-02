from pydantic import BaseModel, Field, field_validator
import re
from exceptions.ValidationExceptions import MissingFieldException, InvalidSignatureException

class UnauthorizeAddress(BaseModel):
    signature: str = Field(..., description="Firma criptográfica del administrador en formato hexadecimal")

    @field_validator("signature")
    @classmethod
    def validate_signature_format(cls, value: str) -> str:
        if not value or not isinstance(value, str):
            raise MissingFieldException()
        
        cleaned = value.strip()
        pattern = re.compile(r"^(0x)?[0-9a-fA-F]{130}$")
        if not pattern.match(cleaned):
            raise InvalidSignatureException()
            
        return cleaned