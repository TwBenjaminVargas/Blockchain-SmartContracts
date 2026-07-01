
class MissingFieldException(ValueError):
    """Se dispara de forma manual si falta algún campo obligatorio o está vacío."""
    pass

class InvalidSignatureException(ValueError):
    """Firma inválida."""
    pass

class InvalidAddressException(ValueError):
    """Dirección inválida."""
    pass

class InvalidCallIdException(ValueError):
    """Identificador de llamado incorrecto."""
    pass

class InvalidProposalException(ValueError):
    """Formato de propuesta incorrecto."""
    pass

class NameTooLongException(ValueError):
    """Nombre demasiado largo."""
    pass

class TitleTooLongException(ValueError):
    """Título demasiado largo."""
    pass

class DescriptionTooLongException(ValueError):
    """Descripción demasiado larga."""
    pass

class TooManyFilesException(ValueError):
    """Demasiados archivos."""
    pass

class ProofTooLongException(ValueError):
    """Prueba de Merkle demasiado larga."""
    pass

class InvalidNameException(ValueError):
    """Nombre inválido."""
    pass

class InvalidTitleException(ValueError):
    """Título inválido."""
    pass