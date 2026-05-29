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

class TextEncodingException(AppBaseException):
    """Lanzada si el texto provisto no puede ser codificado en UTF-8 o excede las restricciones."""
    pass
class BlockchainContractLogicException(AppBaseException):
    """Lanzada cuando un require() o revert() del Smart Contract falla (ej: llamado cerrado)."""
    pass

class BlockchainTransactionException(AppBaseException):
    """Lanzada por problemas de infraestructura (nonce inválido, fondos insuficientes, gas erróneo)."""
    pass

class BlockchainBroadcastException(AppBaseException):
    """Lanzada cuando el nodo RPC rechaza la transmisión de la transacción por problemas de red o infraestructura."""
    pass

class UnderfundedWalletException(AppBaseException):
    """Lanzada específicamente cuando la cuenta interna del servidor se ha quedado sin fondos para pagar el Gas."""
    pass

class NonceCollisionException(AppBaseException):
    """Lanzada cuando ocurre un desfase o duplicación del contador de transacciones (Nonce)."""
    pass

class BlockchainTimeoutException(AppBaseException):
    """Lanzada cuando la transacción tarda más de lo esperado en ser minada (congestionada)."""
    pass

class TransactionRevertedException(AppBaseException):
    """Lanzada cuando la transacción se minó en el bloque pero su ejecución falló (status 0)."""
    pass

class TransactionNotFoundException(AppBaseException):
    """Lanzada cuando el hash provisto no existe en el mempool ni en el histórico del nodo."""
    pass

class BlockchainReadException(AppBaseException):
    """Lanzada cuando falla una consulta de lectura (view) al nodo RPC por problemas de conectividad."""
    pass

class InvalidContractAddressException(AppBaseException):
    """Lanzada cuando se intenta interactuar con una dirección que no es un contrato o no implementa la interfaz requerida."""
    pass