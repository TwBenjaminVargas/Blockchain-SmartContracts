from pydantic import BaseModel, Field, field_validator
from typing import List
import re
import messages as Messages

class ProposalRegister(BaseModel):
    callId: str = Field(..., pattern=r"^0x[a-fA-F0-9]{64}$")
    title: str = Field(...)
    description: str = Field(...)
    files: List[str] = Field(...)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, v: str) -> str:
        if not isinstance(v, str) or not v.rstrip():
            raise ValueError(Messages.INVALID_TITLE)
        cleaned = v.rstrip()
        if len(cleaned.encode("utf-8")) > 512:
            raise ValueError(Messages.TITLE_TOO_LONG)
        return cleaned

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v: str) -> str:
        if not isinstance(v, str):
            v = ""
        cleaned = v.rstrip()
        if len(cleaned.encode("utf-8")) > 4096:
            raise ValueError(Messages.DESCRIPTION_TOO_LONG)
        return cleaned

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: List[str]) -> List[str]:
        if len(v) > 125:
            raise ValueError(Messages.TOO_MANY_FILES)
        if len(v) != len(set(v)):
            raise ValueError(Messages.INVALID_PROPOSAL)
        
        pattern = re.compile(r"^0x[a-fA-F0-9]{64}$")
        for f in v:
            if not isinstance(f, str) or not pattern.match(f):
                raise ValueError(Messages.INVALID_PROPOSAL)
        return [f.lower() for f in v]