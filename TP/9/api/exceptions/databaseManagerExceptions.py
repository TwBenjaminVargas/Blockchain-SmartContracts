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