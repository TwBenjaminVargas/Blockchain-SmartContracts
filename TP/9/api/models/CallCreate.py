from pydantic import BaseModel, field_validator, Field
import messages as Messages

class CallCreate(BaseModel):
    callId: str = Field(
        ...,
        description="Hash keccak256(rlp([title_utf8, description_utf8])) (32 bytes en formato hex con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{64}$",
        examples=["0xb1a9a8360fa47120e6f7723ff4a2fa969a5e4b31a3df6e3532cf97b10255476a"]
    )
    title: str = Field(
        ...,
        description="Título del llamado. No puede superar 512 bytes en UTF-8 ni estar vacío.",
        examples=["Convocatoria de Proyecto Cripto"]
    )
    description: str = Field(
        ...,
        description="Descripción del llamado. No puede superar 4096 bytes en UTF-8.",
        examples=["Esta es una descripción detallada del llamado..."]
    )
    signature: str = Field(
        ...,
        description="Firma criptográfica del creador (65 bytes en formato hex con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{130}$",
        examples=["0x4355c47d63920e8a56e04d34bb4276babdda28d53d142812ba51fe3f65557ef252fec4b4c2049e59b315bab9d7962fec34d28d3615fa2fc7274092b1a16e7fb61b"]
    )


    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError(Messages.INVALID_TITLE)
        
        cleaned_title = value.rstrip()
        
        if not cleaned_title:
            raise ValueError(Messages.INVALID_TITLE)
            
        if len(cleaned_title.encode("utf-8")) > 512:
            raise ValueError(Messages.TITLE_TOO_LONG)
            
        return cleaned_title

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("El campo de descripción debe ser una cadena de texto.")
            
        cleaned_description = value.rstrip()
        
        if len(cleaned_description.encode("utf-8")) > 4096:
            raise ValueError(Messages.DESCRIPTION_TOO_LONG)
            
        return cleaned_description