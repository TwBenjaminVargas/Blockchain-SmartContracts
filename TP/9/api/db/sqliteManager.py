from fastapi import Depends
from services.settings import Settings, get_settings
from sqlmodel import Field, Session, SQLModel, create_engine,select, func
from models.persistence.Call import Call, CallState
from models.persistence.User import User, UserState
from models.persistence.Proposal import Proposal
import logging
import exceptions.databaseManagerExceptions as db_exceptions
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import TypeVar

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)
        
    def _add(self, entity: T) -> T:
        """
        Persiste cualquier entidad heredada de SQLModel en la base de datos de forma segura.

        Raises:
            db_exceptions.RecordAlreadyExistsException: Si se viola una restricción de clave primaria o única.
            db_exceptions.DatabaseWriteException: Si ocurre un bloqueo físico o error de infraestructura.
        """
        try:
            with Session(self.engine) as session:
                session.add(entity)
                session.commit()
                session.refresh(entity)
                return entity
                
        except IntegrityError as integrity_err:
            logger.warning(f"Intento de inserción duplicada: {str(integrity_err)}")
            raise db_exceptions.RecordAlreadyExistsException(
                f"El registro con el identificador provisto ya existe en el sistema."
            )
            
        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico de escritura al persistir: {str(db_err)}")
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
            state=CallState.PENDING
        )
        
        return self._add(nuevo_llamado)
    
    def existUser(self, address: str) -> bool:
        """
        Verifica de forma optimizada si una dirección de usuario ya existe en la base de datos local.

        Raises:
            db_exceptions.InvalidInputTypeException: Si la dirección recibida no es una cadena de texto.
            db_exceptions.DatabaseConnectionException: Si ocurre un fallo en la infraestructura de la DB.
        """
        if not isinstance(address, str) or not address.strip():
            logger.error(f"Tipo de dato inválido o vacío para address en existUser: {type(address)}")
            raise db_exceptions.InvalidInputTypeException("La dirección de usuario debe ser una cadena de texto válida.")

        try:
            with Session(self.engine) as session:
                # Comparamos en minúsculas aplicando func.lower para asegurar consistencia con direcciones hex
                statement = select(func.count()).where(func.lower(User.address) == address.strip().lower())
                count = session.exec(statement).one()

                return count > 0

        except SQLAlchemyError as db_err:
            logger.error(
                f"Fallo crítico de infraestructura al verificar existencia local del usuario '{address}': {str(db_err)}", 
                exc_info=True
            )
            raise db_exceptions.DatabaseConnectionException("Error interno al consultar el registro de usuario local.")
    
    def createPendingUserIfNotExists(self, address: str, name: str, signature: str) -> User:
        """
        Instancia y guarda un usuario con estado 'pending' ÚNICAMENTE si no existe previamente.
        Si ya existe, corta la ejecución de forma temprana lanzando una excepción de negocio.

        Raises:
            db_exceptions.InvalidInputTypeException: Si algún parámetro no es un string válido o está vacío.
            db_exceptions.RecordAlreadyExistsException: Si el usuario ya existe en el almacenamiento local.
            db_exceptions.DatabaseWriteException: Si ocurre un problema al persistir los datos.
        """
        # Validación preventiva
        inputs = {"address": address, "name": name, "signature": signature}
        for field_name, value in inputs.items():
            if not isinstance(value, str) or not value.strip():
                logger.error(f"Parámetro inválido o vacío en createPendingUserIfNotExists: {field_name}={type(value)}")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{field_name}' debe ser una cadena de texto válida.")

        cleaned_address = address.strip()

        #Verificación de existencia previa (Reutiliza tu método optimizado existUserLocal)
        if self.existUserLocal(cleaned_address):
            logger.warning(f"Intento de registro rechazado de forma temprana. El usuario ya existe: {cleaned_address}")
            raise db_exceptions.RecordAlreadyExistsException("El usuario con la dirección provista ya cuenta con un registro en el sistema.")

        nuevo_usuario = User(
            address=cleaned_address,
            name=name.strip(),
            signature=signature.strip(),
            state=UserState.PENDING
        )

        logger.debug(f"Registrando nuevo usuario local PENDING para la wallet: {cleaned_address}")
        return self._add(nuevo_usuario)
    
    def createPendingUser(self, address: str, name: str, signature: str) -> User:
        """
        Instancia y guarda un usuario con estado 'pending'

        Raises:
            db_exceptions.InvalidInputTypeException: Si algún parámetro no es un string válido o está vacío.
            db_exceptions.RecordAlreadyExistsException: Si el usuario ya existe en el almacenamiento local.
            db_exceptions.DatabaseWriteException: Si ocurre un problema al persistir los datos.
        """
        # Validación preventiva
        inputs = {"address": address, "name": name, "signature": signature}
        for field_name, value in inputs.items():
            if not isinstance(value, str) or not value.strip():
                logger.error(f"Parámetro inválido o vacío en createPendingUserIfNotExists: {field_name}={type(value)}")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{field_name}' debe ser una cadena de texto válida.")

        cleaned_address = address.strip()

        nuevo_usuario = User(
            address=cleaned_address,
            name=name.strip(),
            signature=signature.strip(),
            state=UserState.PENDING
        )

        logger.debug(f"Registrando nuevo usuario local PENDING para la wallet: {cleaned_address}")
        return self._add(nuevo_usuario)

    def getUser(self, address: str) -> User | None:
        """
        Recupera una entidad User completa desde el almacenamiento local.
        """
        try:
            with Session(self.engine) as session:
                statement = select(User).where(func.lower(User.address) == address.strip().lower())
                return session.exec(statement).first()
        except SQLAlchemyError as db_err:
            logger.error(f"Error de infraestructura al recuperar el usuario {address}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error al consultar el almacenamiento local.")
        
    def updateExistingUser(self, user: User) -> User:
        """
        Actualiza un usuario existente de forma segura en la base de datos local.
        """
        try:
            with Session(self.engine) as session:
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico al actualizar el usuario '{user.address}': {str(db_err)}")
            raise db_exceptions.DatabaseWriteException("El almacenamiento local no está disponible.")
    
    def existsProposal(self, proposal_id: str) -> bool:
        """Verifica si un proposalId ya existe en el almacenamiento local."""
        try:
            with Session(self.engine) as session:
                statement = select(func.count()).where(Proposal.proposalId == proposal_id.lower())
                return session.exec(statement).one() > 0
        except SQLAlchemyError as db_err:
            logger.error(f"Error al verificar existencia de propuesta {proposal_id}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error de base de datos.")

    def register_proposal(self, call_id: str, proposal_id: str, title: str, title_hash: str, 
                          description: str, description_hash: str, files: list[str], proofs: dict) -> Proposal:
        """Crea el objeto Proposal serializando las estructuras complejas y las persiste."""
        import json
        
        new_proposal = Proposal(
            callId=call_id.lower(),
            proposalId=proposal_id.lower(),
            title=title,
            titleHash=title_hash,
            description=description,
            descriptionHash=description_hash,
            filesJson=json.dumps(files),
            proofsJson=json.dumps(proofs)
        )
        return self._add(new_proposal)

    def get_proof(self, proposal_id: str) -> dict | None:
        """Recupera la entidad para procesamiento interno."""
        try:
            with Session(self.engine) as session:
                statement = select(Proposal).where(Proposal.proposalId == proposal_id.lower())
                return session.exec(statement).first()
        except SQLAlchemyError as db_err:
            logger.error(f"Fallo al leer propuesta del llamado {proposal_id}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error de lectura local.")

    def get_proof_json(self, proposal_id: str) -> dict:
        """Devuelve directamente las pruebas de Merkle mapeadas desde el JSON persistido."""
        import json
        proposal = self.get_proof(proposal_id)
        if not proposal:
            return {}
        return json.loads(proposal.proofsJson)

    def getCall(self, call_id: str) -> Call | None:
        """
        Busca un llamado registrado localmente por su callId.
        Retorna la entidad Call si existe, o None si no es encontrada.
        """
        try:
            with Session(self.engine) as session:
                statement = select(Call).where(Call.callId == call_id.lower())
                return session.exec(statement).first()
        except SQLAlchemyError as db_err:
            logger.error(f"Error al recuperar el llamado {call_id}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error de lectura en el almacenamiento local.")

def get_db_manager(settings: Settings = Depends(get_settings)) -> DBManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    """
    return DBManager(
        db_path=settings.db_path
    )