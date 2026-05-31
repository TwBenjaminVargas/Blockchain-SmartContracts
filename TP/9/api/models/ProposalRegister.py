from pydantic import BaseModel, Field, field_validator
from typing import List
import re
from exceptions.ValidationExceptions import (
    InvalidTitleException,
    TitleTooLongException,
    DescriptionTooLongException,
    TooManyFilesException,
    InvalidProposalException
)

class ProposalRegister(BaseModel):
    callId: str = Field(..., pattern=r"^0x[a-fA-F0-9]{64}$")
    title: str = Field(...)
    description: str = Field(...)
    files: List[str] = Field(...)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, v: str) -> str:
        # Si no es texto o queda vacío al quitar espacios a la derecha -> Título inválido
        if not isinstance(v, str) or not v.rstrip():
            raise InvalidTitleException()
            
        cleaned = v.rstrip()
        # Validación de bytes UTF-8 para el límite estricto
        if len(cleaned.encode("utf-8")) > 512:
            raise TitleTooLongException()
            
        return cleaned

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v: str) -> str:
        if not isinstance(v, str):
            v = ""
            
        cleaned = v.rstrip()
        # Validación de bytes UTF-8 para la descripción
        if len(cleaned.encode("utf-8")) > 4096:
            raise DescriptionTooLongException()
            
        return cleaned

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: List[str]) -> List[str]:
        # El árbol Merkle no puede superar las 128 hojas en total (límite de archivos: 125)
        if len(v) > 125:
            raise TooManyFilesException()
            
        # Comprobar duplicados dentro de la lista de archivos usando sets
        if len(v) != len(set(v)):
            raise InvalidProposalException()
        
        pattern = re.compile(r"^0x[a-fA-F0-9]{64}$")
        for f in v:
            # Cada hash de archivo debe ser una cadena hexadecimal keccak256 válida
            if not isinstance(f, str) or not pattern.match(f):
                raise InvalidProposalException()
                
        return [f.lower() for f in v]