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
    
    #! Problema de 513 bytes recibidos con test test_update_registration_name_limit
    @field_validator("name", mode="before")
    @classmethod
    def validate_and_clean_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise InvalidNameException()
        #* Descomentar para ver el problema de los 513 bytes recibidos en el test test_update_registration_name_limit
        #print(f"BYTES: {len(value.encode('utf-8'))}")
        #print(f"CHARS: {len(value)}")
        #print(f"ULTIMOS 3 CHARS: {[hex(ord(c)) for c in value[-3:]]}")

        cleaned_value = value.replace("\n", "").replace("\r", "").rstrip()
        if not cleaned_value.strip():
            raise InvalidNameException()
        if len(cleaned_value.encode("utf-8")) > 512:
            raise NameTooLongException()
        return cleaned_value