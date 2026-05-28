from fastapi import Depends
from services.settings import Settings, get_settings
from sqlmodel import Field, Session, SQLModel, create_engine,select, func
from models.persistence.Call import Call
from models.persistence.User import User
import logging
import exceptions.databaseManagerExceptions as db_exceptions
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)
        
    def addCall(self, call: Call) -> Call:
        """
        Persiste un objeto 'Call' en SQLite de forma segura.

        Raises:
            db_exceptions.RecordAlreadyExistsException: Si el callId ya está registrado (Primary Key Duplicated).
            db_exceptions.DatabaseWriteException: Si ocurre un bloqueo de archivo u otro error de escritura.
        """
        try:
            with Session(self.engine) as session:
                session.add(call)
                session.commit()
                session.refresh(call)
                return call
                
        except IntegrityError as integrity_err:
            logger.warning(f"Intento de inserción duplicada para el CallId '{call.callId}': {str(integrity_err)}")
            raise db_exceptions.RecordAlreadyExistsException("El identificador del llamado ya se encuentra registrado.")
            
        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico de escritura al persistir CallId '{call.callId}': {str(db_err)}", exc_info=True)
            raise db_exceptions.DatabaseWriteException("El almacenamiento local no está disponible o se encuentra bloqueado.")
    
    def existsCall(self, call_id: str) -> bool:
        """
        Verifica si un callId ya existe en la API local usando SQLModel.
        Optimizado para contar registros en lugar de traer toda la fila a memoria.

        Raises:
            DatabaseConnectionException: Si ocurre un fallo crítico en el motor de la DB.
        """
        try:
            with Session(self.engine) as session:
                # Contamos las ocurrencias de ese callId (0 o 1)
                statement = select(func.count()).where(Call.callId == call_id)
                count = session.exec(statement).one()

                return count > 0

        except SQLAlchemyError as db_err:
            logger.error(
                f"Fallo crítico de infraestructura al verificar existencia de CallId '{call_id}': {str(db_err)}", 
                exc_info=True
            )
            raise db_exceptions.DatabaseConnectionException("Error interno al consultar el almacenamiento local.")

    def createPendingCall(self, call_id: str, title: str, description: str, signature: str, creator_address: str) -> Call:
        """
        Instancia y persiste un nuevo objeto 'Call' con estado inicial 'PENDING'.
        
        Raises:
            db_exceptions.InvalidInputTypeException: Si alguno de los parámetros de entrada no es una cadena de texto.
            db_exceptions.RecordAlreadyExistsException: Si el call_id ya existe en el sistema.
            db_exceptions.DatabaseWriteException: Si el motor de base de datos falla al escribir.
        """
        # Validación preventiva
        inputs = {"call_id": call_id, "title": title, "description": description, "signature": signature, "creator_address": creator_address}
        for name, value in inputs.items():
            if not isinstance(value, str) or not value.strip():
                logger.error(f"Parámetro inválido o vacío detectado en createPendingCall: {name}={type(value)}")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{name}' debe ser una cadena de texto válida y no estar vacío.")

        # Instanciamos el modelo de SQLModel
        nuevo_llamado = Call(
            callId=call_id.strip(),
            title=title.strip(),
            description=description.strip(),
            signature=signature.strip(),
            creator=creator_address.strip(),
            state="PENDING"
        )
        
        # Dejamos que addCall maneje de forma transparente y granular las excepciones de la DB
        return self.addCall(nuevo_llamado)
    
    def existUserLocal(self, address: str) -> bool:
        """Helper para verificar si el usuario ya tiene un registro local previo"""
        return self.session.query(User).filter(User.address.lower() == address.lower()).first() is not None
        

def get_db_manager(settings: Settings = Depends(get_settings)) -> DBManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    """
    return DBManager(
        db_path=settings.db_path
    )