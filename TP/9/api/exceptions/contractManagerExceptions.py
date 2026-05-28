from .AppBaseException import AppBaseException

class InvalidInputTypeException(AppBaseException):
    """Lanzada cuando el título o la descripción no son cadenas de texto."""
    pass

class CryptographicHashingException(AppBaseException):
    """Lanzada si ocurre un fallo crítico al codificar RLP o calcular Keccak."""
    pass

class NodeRPCException(AppBaseException):
    """Lanzada cuando falla la comunicación con el nodo de Ethereum o el proveedor RPC."""
    pass