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