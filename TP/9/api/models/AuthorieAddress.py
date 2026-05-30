from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError
import re
import messages as Messages

class AuthorizeAddress(BaseModel):
    signature: str = Field(..., description="Firma criptográfica del administrador en formato hexadecimal")

    @field_validator("signature")
    @classmethod
    def validate_signature_format(cls, value: str) -> str:
        if not value or not isinstance(value, str):
            raise PydanticCustomError("value_error", Messages.MISSING_FIELD)
        
        cleaned = value.strip()
        pattern = re.compile(r"^(0x)?[0-9a-fA-F]{130}$")
        if not pattern.match(cleaned):
            raise PydanticCustomError("value_error", Messages.INVALID_SIGNATURE)
            
        return cleaned