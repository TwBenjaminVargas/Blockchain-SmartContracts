from pydantic import BaseModel, Field, field_validator
from exceptions.ValidationExceptions import InvalidNameException, NameTooLongException

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
        examples=["0xd72c1655fde0f5179687dbf4b6e3c25d45f24d819d2b93bdf5d34ab86967c387015b863608371d925cd1d3c9796cad0b486e38a9938bd38820e0e24ad70f567b1b"]
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_and_clean_name(cls, value: str) -> str:
        # Si el nombre no es un string, lo consideramos inválido
        if not isinstance(value, str):
            raise InvalidNameException()
        
        cleaned = value.rstrip()
        
        # Si quedó vacío luego de remover espacios en blanco a la derecha
        if not cleaned:
            raise InvalidNameException()
            
        # Validación estricta del límite midiendo la longitud en bytes UTF-8
        if len(cleaned.encode("utf-8")) > 512:
            raise NameTooLongException()
            
        return cleaned