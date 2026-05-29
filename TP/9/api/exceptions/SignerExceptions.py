from .AppBaseException import AppBaseException

class InvalidSignatureException(AppBaseException):
    """Lanzada cuando la firma no es válida o no corresponde al mensaje."""
    pass

class CryptographicSigningException(AppBaseException):
    """Lanzada cuando el firmado offline falla debido a claves privadas inválidas o comprometidas."""
    pass

class InvalidTransactionStructureException(AppBaseException):
    """Lanzada cuando el diccionario de la transacción está mal estructurado o le faltan campos esenciales."""
    pass