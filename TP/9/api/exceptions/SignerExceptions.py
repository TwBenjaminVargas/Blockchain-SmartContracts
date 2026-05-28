from .AppBaseException import AppBaseException

class InvalidSignatureException(AppBaseException):
    """Lanzada cuando la firma no es válida o no corresponde al mensaje."""
    pass