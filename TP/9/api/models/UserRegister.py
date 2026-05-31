from pydantic import BaseModel, Field, field_validator
from exceptions.ValidationExceptions import InvalidNameException, NameTooLongException

class UserRegister(BaseModel):
    address: str = Field(
        ...,
        description="Dirección de Ethereum del solicitante (20 bytes en formato hex con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{40}$",
        examples=["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"]
    )
    name: str = Field(
        ...,
        description="Nombre del solicitante. No puede superar 512 bytes en UTF-8 ni estar vacío.",
        examples=["Benjamín Solana"]
    )
    signature: str = Field(
        ...,
        description="Firma criptográfica del solicitante (65 bytes en formato hex con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{130}$",
        examples=["0xd72c1655fde0f5179687dbf4b6e3c25d45f24d819d2b93bdf5d34ab86967c387015b863608371d925cd1d3c9796cad0b486e38a9938bd38820e0e24ad70f567b1b"]
    )

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        # Si el valor ingresado ni siquiera es una cadena de texto
        if not isinstance(value, str):
            raise InvalidNameException()
        
        cleaned_name = value.rstrip()
        
        # Si el campo queda vacío tras remover los espacios finales en blanco
        if not cleaned_name:
            raise InvalidNameException()
            
        # Validación estricta midiendo los bytes reales codificados en UTF-8
        if len(cleaned_name.encode("utf-8")) > 512:
            raise NameTooLongException()
            
        return cleaned_name