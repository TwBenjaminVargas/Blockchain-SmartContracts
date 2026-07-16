from pydantic import BaseModel, field_validator, Field
from exceptions.ValidationExceptions import (
    InvalidTitleException, 
    TitleTooLongException, 
    DescriptionTooLongException
)

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
    
    domain: str = Field(
        ...,
        description="Nombre de dominio ENS del usuario registrado.",
        pattern=r"^[a-z0-9.-]+\.[a-z]{2,}$",
        examples=["pepe.usuarios.cfp", "benja.eth"]
    )

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: str) -> str:
        # Si no se envía un string o el campo está vacío al quitar espacios finales, es título inválido
        if not isinstance(value, str):
            raise InvalidTitleException()
        
        cleaned_title = value.rstrip()
        
        if not cleaned_title:
            raise InvalidTitleException()
            
        # Validación de longitud estricta en bytes UTF-8
        if len(cleaned_title.encode("utf-8")) > 512:
            raise TitleTooLongException()
            
        return cleaned_title

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: str) -> str:
        # Si no se envía una descripción de tipo string, la tratamos como vacía para quitar espacios
        if not isinstance(value, str):
            value = ""
            
        cleaned_description = value.rstrip()
        
        # Validación de longitud estricta en bytes UTF-8
        if len(cleaned_description.encode("utf-8")) > 4096:
            raise DescriptionTooLongException()
            
        return cleaned_description