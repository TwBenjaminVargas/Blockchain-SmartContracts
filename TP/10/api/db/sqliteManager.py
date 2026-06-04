import json
from services.settings import get_settings
from sqlmodel import Session, SQLModel, create_engine,select, func
from models.persistence.Call import Call, CallState
from models.persistence.User import User, UserState
from models.persistence.Proposal import Proposal
from models.persistence.SyncState import SyncState
import logging
import exceptions.databaseManagerExceptions as db_exceptions
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import TypeVar, Optional, Tuple
from functools import lru_cache

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        settings = get_settings()
        self.db_path = settings.db_path
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
        inputs = {"call_id": call_id, "title": title, "signature": signature, "creator_address": creator_address}
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
        """
        inputs = {"address": address, "name": name, "signature": signature}
        for field_name, value in inputs.items():
            if not isinstance(value, str) or not value.strip():
                logger.error(f"Parámetro inválido o vacío en createPendingUserIfNotExists: {field_name}={type(value)}")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{field_name}' debe ser una cadena de texto válida.")

        cleaned_address = address.strip()

        if self.existUser(cleaned_address):
            logger.warning(f"Intento de registro rechazado de forma temprana. El usuario ya existe: {cleaned_address}")
            raise db_exceptions.RecordAlreadyExistsException("El usuario con la dirección provista ya cuenta con un registro en el sistema.")

        nuevo_usuario = User(
            address=cleaned_address,
            name=name.strip(),
            signature=signature.strip(),
            state=UserState.PENDING,
            nonce=1
        )

        logger.debug(f"Registrando nuevo usuario local PENDING para la wallet: {cleaned_address}")
        return self._add(nuevo_usuario)
 
    def createAdminUser(self, address: str) -> User:
            """
            Instancia y guarda un usuario administrador
            """

            if not isinstance(address, str) or not address.strip():
                logger.error(f"Parámetro inválido o vacío en createAdminUser")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{address}' debe ser una cadena de texto válida.")

            cleaned_address = address.strip()

            if self.existUser(cleaned_address):
                logger.warning(f"Intento de registro rechazado de forma temprana. El usuario ya existe: {cleaned_address}")
                raise db_exceptions.RecordAlreadyExistsException("El usuario con la dirección provista ya cuenta con un registro en el sistema.")

            nuevo_usuario = User(
                address=cleaned_address,
                name="admin",
                signature="0x0",
                state=UserState.AUTHORIZED,
                nonce=1
            )

            logger.debug(f"Registrando usuario admin local con la wallet: {cleaned_address}")
            return self._add(nuevo_usuario)
    
    def get_all_users(self) -> list[User]:
        """
        Recupera todos los usuarios registrados en el sistema usando SQLModel.

        Raises:
            db_exceptions.DatabaseReadException: Si ocurre un fallo crítico al consultar.
        """
        try:
            with Session(self.engine) as session:
                statement = select(User)
                # .all() devuelve una lista de objetos User
                users = session.exec(statement).all()
                return list(users)

        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico al recuperar todos los usuarios: {str(db_err)}", exc_info=True)
            raise db_exceptions.DatabaseConnectionException("Error interno al leer los usuarios del almacenamiento local.")
    
    def createUser(self, address: str, name: str, signature: str,description: str | None = None, state: UserState = UserState.PENDING) -> User:
        """
        Instancia y guarda un usuario con estado 'pending'
        """
        inputs = {"address": address, "name": name, "signature": signature}
        for field_name, value in inputs.items():
            if not isinstance(value, str) or not value.strip():
                logger.error(f"Parámetro inválido o vacío en createUser: {field_name}={type(value)}")
                raise db_exceptions.InvalidInputTypeException(f"El campo '{field_name}' debe ser una cadena de texto válida.")

        cleaned_address = address.strip()

        nuevo_usuario = User(
            address=cleaned_address,
            name=name.strip(),
            description= description.strip() if description else None,
            signature=signature.strip(),
            state=state,
            nonce=1
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
    
    def get_pending_and_registered_users(self) -> list[User]:
        """
        Recupera todos los usuarios cuyo estado local sea PENDING o REGISTERED.
        Representan las solicitudes de autorización pendientes para el sistema.
        """
        try:
            with Session(self.engine) as session:
                # Usamos .in_() para filtrar por múltiples estados
                statement = select(User).where(
                    User.state.in_([UserState.PENDING, UserState.REGISTERED])
                )
                users = session.exec(statement).all()
                return list(users)

        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico al recuperar solicitudes pendientes/registradas: {str(db_err)}", exc_info=True)
            raise db_exceptions.DatabaseConnectionException("Error interno al leer usuarios de la base de datos.")
    
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

    def register_proposal(
        self, 
        call_id: str, 
        proposal_id: str, 
        title: str, 
        title_hash: str, 
        description: str, 
        description_hash: str, 
        files: list, 
        proofs: dict,
        created: int,
        blocknumber: int,
        sender: str
    ):
        import json
        new_proposal = Proposal(
            proposalId=proposal_id.lower(),
            callId=call_id.lower(),
            title=title,
            titleHash=title_hash.lower(),
            description=description,
            descriptionHash=description_hash.lower(),
            filesJson=json.dumps(files),
            proofsJson=json.dumps(proofs),
            created=created,
            blocknumber=blocknumber,
            sender=sender.lower()
        )
        return self._add(new_proposal)

    def get_proof(self, proposal_id: str) -> dict | None:
        """Recupera la prueba de la base de datos y la convierte a un diccionario real de Python."""
        try:
            with Session(self.engine) as session:
                statement = select(Proposal).where(Proposal.proposalId == proposal_id.lower())
                proposal_record = session.exec(statement).first()

                if not proposal_record or not proposal_record.proofsJson:
                    return None


                if isinstance(proposal_record.proofsJson, str):
                    return json.loads(proposal_record.proofsJson)

                # Si ORM ya lo parseó automáticamente, lo devolvemos directo
                return proposal_record.proofsJson

        except SQLAlchemyError as db_err:
            logger.error(f"Fallo al leer propuesta del llamado {proposal_id}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error de lectura local.")
        except json.JSONDecodeError as json_err:
            logger.error(f"Error crítico de parseo: El campo proofsJson para {proposal_id} está mal formado: {str(json_err)}")
            return None
    
    def get_proof_json(self, proposal_id: str) -> dict:
        """Devuelve directamente las pruebas de Merkle mapeadas desde el JSON persistido."""
        import json
        proposal = self.get_proof(proposal_id)
        if not proposal:
            return {}
        return json.loads(proposal.proofsJson)

    def getProposal(self, proposal_id: str) -> Proposal | None:
        """
        Busca y retorna una propuesta por su ID (raíz de Merkle) desde la BD local.
        """
        try:
            with Session(self.engine) as session:
                statement = select(Proposal).where(Proposal.proposalId == proposal_id.lower())
                results = session.exec(statement)
                return results.first()
        except Exception as e:
            logger.error(f"Error al consultar la propuesta {proposal_id} en la base de datos: {str(e)}")
            raise db_exceptions.DatabaseConnectionException("Error de conexión con el almacenamiento local.")
           
    def get_proposal_with_call_state(self, call_id: str, proposal_id: str) -> Optional[Tuple[Proposal, int]]:
        """
        Recupera una propuesta vinculada a un llamado y obtiene de forma eficiente 
        el 'closingTime' desde la tabla de llamados en un solo viaje a la base de datos (JOIN).

        :param call_id: Hash identificador del llamado (0x...)
        :param proposal_id: Hash raíz de Merkle de la propuesta (0x...)
        :return: Una tupla (Proposal, closingTime) si existe coincidencia, de lo contrario None.
        """
        try:
            logger.debug(
                f"Ejecutando JOIN en BD para Proposal: {proposal_id} y CallId: {call_id}"
            )
            with Session(self.engine) as session:
                statement = (
                    select(Proposal, Call.closingTime)
                    .join(Call, Proposal.callId == Call.callId)
                    .where(
                        Proposal.callId == call_id.lower(),
                        Proposal.proposalId == proposal_id.lower()
                    )
                )
                result = session.exec(statement).first()

            if result:
                logger.debug(f"Propuesta {proposal_id} y su closingTime encontrados con éxito localmente.")
            else:
                logger.warning(f"No se encontró ninguna coincidencia en BD para la combinación CallId/Proposal provista.")

            return result

        except Exception as e:
            logger.error(
                f"Fallo crítico de persistencia al intentar recuperar propuesta con JOIN {proposal_id}: {str(e)}", 
                exc_info=True
            )
            raise db_exceptions.DatabaseConnectionException(
                "Error de infraestructura al consultar el almacenamiento local de propuestas."
            )

    def getCall(self, call_id: str) -> Call | None:
        """
        Busca un llamado registrado localmente por su callId.
        Retorna la entidad Call si existe, o None si no es encontrada.
        """
        try:
            with Session(self.engine) as session:
                statement = select(Call).where(Call.callId == call_id)
                return session.exec(statement).first()
        except SQLAlchemyError as db_err:
            logger.error(f"Error al recuperar el llamado {call_id}: {str(db_err)}")
            raise db_exceptions.DatabaseConnectionException("Error de lectura en el almacenamiento local.")

    def incrementUserNonce(self, address: str) -> int:
        """
        Incrementa el nonce de un usuario en 1 reutilizando la lógica interna.
        Retorna el nuevo valor asignado.
        """
        user = self.getUser(address)
        if not user:
            raise db_exceptions.UserNotFoundException("La dirección solicitada no está registrada en el sistema.")
        
        if user.nonce >= 2**32 - 1:
            raise db_exceptions.NonceOverflowException("Se ha alcanzado el límite máximo para el valor del nonce.")
            
        user.nonce += 1
        self.updateExistingUser(user)
        return user.nonce

    def authorizeUser(self, address: str) -> User:
        """
        Modifica el estado de un usuario local al valor AUTHORIZED reutilizando la lógica interna.
        """
        user = self.getUser(address)
        if not user:
            raise db_exceptions.UserNotFoundException("La dirección solicitada no está registrada en el sistema.")
        
        user.state = UserState.AUTHORIZED
        return self.updateExistingUser(user)
    
    def unauthorizeUser(self, address: str, created_count: int) -> User | None:
        """
        Revoca la autorización de un usuario local.
        Si posee llamados creados en el sistema se archiva, de lo contrario se elimina la cuenta.
        """
        cleaned_address = address.strip().lower()
        user = self.getUser(cleaned_address)
        if not user:
            raise db_exceptions.UserNotFoundException("La dirección solicitada no está registrada en el sistema.")
        
        # Si no tiene llamados creados, se elimina el registro del usuario por completo
        if created_count == 0:
            try:
                with Session(self.engine) as session:
                    session.add(user)
                    session.delete(user)
                    session.commit()
                logger.debug(f"Usuario sin llamados eliminado del almacenamiento local: {cleaned_address}")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Fallo al eliminar el usuario {cleaned_address} sin llamados: {str(e)}")
                raise db_exceptions.DatabaseWriteException("Error interno al intentar eliminar el registro local.")
        
        user.state = UserState.ARCHIVED
        return self.updateExistingUser(user)
    
    def get_or_create_last_block(self, fallback_block: int) -> int:
        """
        Recupera el último bloque guardado en 'sync_state'. 
        Si no existe, lo inicializa con el fallback_block provisto.
        """
        try:
            with Session(self.engine) as session:
                state = session.exec(select(SyncState).where(SyncState.id == 1)).first()
                if state:
                    return state.last_scanned_block
                
                new_state = SyncState(id=1, last_scanned_block=fallback_block)
                session.add(new_state)
                session.commit()
                return fallback_block
        except SQLAlchemyError as e:
            logger.error(f"Fallo de DB al leer/inicializar sync_state: {str(e)}")
            return fallback_block

    def update_last_block(self, block_number: int):
        """
        Actualiza el número del último bloque procesado con éxito.
        """
        try:
            with Session(self.engine) as session:
                state = session.exec(select(SyncState).where(SyncState.id == 1)).first()
                if state:
                    state.last_scanned_block = block_number
                    session.add(state)
                    session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Fallo de DB al actualizar checkpoint al bloque {block_number}: {str(e)}")
    
    def updateExistingCall(self, call: Call) -> Call:
        """
        Guarda los cambios de un objeto Call ya modificado en la base de datos local.
        """
        try:
            with Session(self.engine) as session:
                session.add(call)
                session.commit()
                session.refresh(call)
                logger.info(f"Llamado '{call.callId}' guardado con éxito en el almacenamiento local.")
                return call
        except SQLAlchemyError as db_err:
            logger.error(f"Fallo crítico al guardar el llamado '{call.callId}': {str(db_err)}")
            raise db_exceptions.DatabaseWriteException("El almacenamiento local no está disponible para actualizar el llamado.")
    
    def get_creators(self,contract_creators: list[str]) -> tuple[list[str], list[UserState]]:
        """
        Compara una lista de creadores de Blockchain contra la Base de Datos.

        Retorna:
            - Una tupla: (list[str], list[UserState])
            - El primer elemento son las direcciones que FALTAN (en minúsculas).
            - El segundo elemento son los OBJETOS completos de la BD que SÍ ESTÁN.
        """
        
        creators_lower = [addr.lower() for addr in contract_creators]
        try:
            with Session(self.engine) as session:
                # Buscamos los usuarios que SÍ están en el arreglo
                statement = select(User).where(
                    func.lower(User.address).in_(creators_lower)
                )
                existing_users_models = session.exec(statement).all()

                existing_addresses_set = {user.address.lower() for user in existing_users_models}
                
                missing_creators = list(set(creators_lower) - existing_addresses_set)
                
                logger.debug(f"Comparación de creadores: {len(creators_lower)} en contrato, {len(existing_users_models)} encontrados en BD, {len(missing_creators)} faltantes.")

                return missing_creators, existing_users_models

        except Exception as e:
            logger.error(f"Error crítico al verificar estado de creadores en la BD: {str(e)}", exc_info=True)
            raise db_exceptions.DatabaseReadException(
                "Error al consultar el estado de los creadores en la base de datos local."
            )
      
@lru_cache()
def get_db_manager() -> DBManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    """
    return DBManager()