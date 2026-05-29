from pydantic import BaseModel, Field, field_validator
import messages as Messages

class UserPatch(BaseModel):
    name: str = Field(
        ...,
        description="Nuevo nombre del solicitante",
        examples=["Benjamín Solana"]
    )
    signature: str = Field(
        ...,
        description="Firma criptográfica de los datos concatenados",
        pattern=r"^0x[a-fA-F0-9]{130}$",
        examples=["0xd72c1655fde0f5179687db..."]
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_and_clean_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("El nombre debe ser una cadena de texto.")
        
        cleaned = value.rstrip()
        if not cleaned:
            raise ValueError(Messages.INVALID_NAME)
            
        if len(cleaned.encode("utf-8")) > 512:
            raise ValueError(Messages.NAME_TOO_LONG)
            
        return cleaned