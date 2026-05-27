# Contratos de API con validación avanzada usando Pydantic
from datetime import datetime
from pydantic import BaseModel, Field

class CFPSchema(BaseModel):
    callId: str = Field(
        ...,
        description="Hash de la transacción (32 bytes en formato hexadecimal con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{64}$",
        examples=["0xb1a9a8360fa47120e6f7723ff4a2fa969a5e4b31a3df6e3532cf97b10255476a"]
    )
    closing_time: datetime = Field(
        ...,
        description="Fecha y hora del cierre de convocatoria en formato ISO 8601",
        examples=["2026-05-20T18:00:00Z"],
        alias="closingTime"
    )
    
    signature: str = Field(
        ...,
        description="Firma criptográfica ECDSA (65 bytes en formato hexadecimal con prefijo 0x)",
        pattern=r"^0x[a-fA-F0-9]{130}$",  # 65 bytes = 130 caracteres hexadecimales
        examples=["0x4355c47d63920e8a56e04d34bb4276babdda28d53d142812ba51fe3f65557ef252fec4b4c2049e59b315bab9d7962fec34d28d3615fa2fc7274092b1a16e7fb61b"]
    )

class RegisterSchema(BaseModel):
    address: str = Field(
        ...,
        description="Dirección del solicitante en formato hexadecimal.",
        pattern=r"^0x[a-fA-F0-9]{40}$",
        examples=["0x3Bdd62278057288b1F486cBD775986AD042F5E4A"]
    )
    
    signature: str = Field(
        ...,
        description="Firma de la dirección del contrato EIP-191 (65 bytes -> 130 caracteres hex + 0x).",
        pattern=r"^0x[a-fA-F0-9]{130}$",
        examples=["0x473686f1d3fb6e10aa68d1e31d997d8848b27feb2241c0088ce93b6f3927f48b49544062286ce7e05afa2f8d8b2d0609110eb9964a3704c96689cc8454dc028f1b"]
    )

class RegisterProposalSchema(BaseModel):
    callId: str = Field(
        ...,
        description="Hash hexadecimal de 32 bytes que identifica unívocamente al llamado.",
        pattern=r"^0x[a-fA-F0-9]{64}$",
        examples=["0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"]
    )
    
    proposal: str = Field(
        ...,
        description="Hash hexadecimal de 32 bytes que identifica unívocamente a la propuesta.",
        pattern=r"^0x[a-fA-F0-9]{64}$",
        examples=["0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba"]
    )