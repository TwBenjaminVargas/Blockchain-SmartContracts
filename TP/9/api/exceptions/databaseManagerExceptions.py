from .AppBaseException import AppBaseException

class DatabaseConnectionException(AppBaseException):
    """Lanzada cuando SQLite está bloqueado, corrupto o inaccesible."""
    pass

class DatabaseWriteException(AppBaseException):
    """Lanzada cuando falla la escritura física en la base de datos (bloqueos, corrupción)."""
    pass

class InvalidInputTypeException(AppBaseException):
    """Lanzada cuando alguno de los parámetros de entrada no es valido """
    pass

class RecordAlreadyExistsException(AppBaseException):
    """Lanzada cuando se intenta insertar un registro con una clave primaria o única duplicada."""
    pass

class TooManyFilesException(AppBaseException):
    """Lanzada cuando la lista de archivos supera los 125 elementos."""
    pass

class InvalidProposalDataException(AppBaseException):
    """Lanzada cuando un hash de archivo está malformado o duplicado."""
    pass

class CallNotFoundException(AppBaseException):
    """Lanzada cuando un llamado consultado no existe en el almacenamiento local."""
    pass
class ProposalNotFoundException(AppBaseException):
    """Lanzada cuando la propuesta solicitada no existe en la base de datos local."""
    pass