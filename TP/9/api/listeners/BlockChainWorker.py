import asyncio
import logging
from models.persistence.Call import CallState
from models.persistence.User import UserState
from services.contractManager import get_contract_manager
from db.sqliteManager import get_db_manager

logger = logging.getLogger(__name__)

class BlockchainWorker:
    def __init__(self):

        self.contract_manager = get_contract_manager()
        self.db_manager = get_db_manager()
        

        self.w3 = self.contract_manager.w3
        self.contract = self.contract_manager.contract
        
        # Control de estado del hilo asíncrono
        self.running = False

    async def start_worker(self, interval_seconds: int = 3):
        """
        Bucle infinito asíncrono (Polling) encargado de coordinar el escaneo de bloques.
        """
        self.running = True
        logger.info("Worker de Blockchain iniciado en segundo plano.")

        # Obtiene el punto de partida desde la DB, Fallback al bloque actual si está vacío.
        current_blockchain_block = self.w3.eth.block_number
        from_block = self.db_manager.get_or_create_last_block(fallback_block=current_blockchain_block) + 1

        while self.running:
            try:
                current_latest_block = self.w3.eth.block_number

                # Si no hay bloques nuevos que procesar, salta la iteración
                if from_block > current_latest_block:
                    await asyncio.sleep(interval_seconds)
                    continue

                logger.debug(f"Escaneando eventos en rango: [{from_block} -> {current_latest_block}]")

                # Disparar la captura secuencial de cada evento
                await self._process_creator_registered(from_block, current_latest_block)
                await self._process_creator_authorized(from_block, current_latest_block)
                await self._process_creator_unauthorized(from_block, current_latest_block)
                await self._process_cfp_created(from_block, current_latest_block)

                # Guardar progreso tras éxito de la tanda (Checkpointing en DB)
                self.db_manager.update_last_block(current_latest_block)
                from_block = current_latest_block + 1

            except Exception as e:
                logger.error(f"Fallo temporal detectado en el bucle del Worker: {str(e)}", exc_info=True)
            
            # Cede el procesador a la API antes de la siguiente vuelta
            await asyncio.sleep(interval_seconds)

    def stop_worker(self):
        """
        Solicita la detención pacífica del Worker.
        """
        self.running = False
        logger.info("Worker de Blockchain deteniendo bucles de fondo...")

    async def _process_creator_registered(self, from_block: int, to_block: int):
        """
        Filtra y procesa 'event CreatorRegistered(address indexed creator)'.
        Busca el usuario local por su dirección y actualiza su estado a REGISTERED.
        """
        event_filter = self.contract.events.CreatorRegistered.create_filter(from_block=from_block, to_block=to_block)
        
        for event in event_filter.get_all_entries():
            try:
                creator_address = event.args.creator.lower()
                logger.info(f"Evento on-chain capturado: CreatorRegistered -> {creator_address}")
                
                local_user = self.db_manager.getUser(creator_address)
                
                if not local_user:
                    logger.warning(
                        f"Usuario on-chain {creator_address} ignorado: no se encontró registro previo en la DB local."
                    )
                    continue
                
                local_user.state = UserState.REGISTERED
                
                self.db_manager.updateExistingUser(local_user)
                logger.info(f"Usuario {creator_address} sincronizado exitosamente al estado REGISTERED.")
                
            except Exception as event_err:
                logger.error(
                    f"Error inesperado al procesar un evento individual CreatorRegistered: {str(event_err)}", 
                    exc_info=True
                )

    async def _process_creator_authorized(self, from_block: int, to_block: int):
        """
        Filtra y procesa 'event CreatorAuthorized(address indexed creator)'.
        Busca el usuario local por su dirección y actualiza su estado a AUTHORIZED.
        """
        event_filter = self.contract.events.CreatorAuthorized.create_filter(from_block=from_block, to_block=to_block)
        
        for event in event_filter.get_all_entries():
            try:
                creator_address = event.args.creator.lower()
                logger.info(f"Evento on-chain capturado: CreatorAuthorized -> {creator_address}")
                
                local_user = self.db_manager.getUser(creator_address)
                
                if not local_user:
                    logger.warning(
                        f"Usuario on-chain {creator_address} ignorado en autorización: no existe en la DB local."
                    )
                    continue
                
                local_user.state = UserState.AUTHORIZED
                
                self.db_manager.updateExistingUser(local_user)
                logger.info(f"Usuario {creator_address} sincronizado exitosamente al estado AUTHORIZED.")
                
            except Exception as event_err:
                logger.error(
                    f"Error inesperado al procesar un evento individual CreatorAuthorized: {str(event_err)}", 
                    exc_info=True
                )

    async def _process_creator_unauthorized(self, from_block: int, to_block: int):
        """
        Filtra y procesa 'event CreatorUnauthorized(address indexed creator)'.
        Verifica la existencia del usuario localmente y delega en el DBManager para archivar o eliminar.
        """
        event_filter = self.contract.events.CreatorUnauthorized.create_filter(from_block=from_block, to_block=to_block)
        
        for event in event_filter.get_all_entries():
            try:
                creator_address = event.args.creator.lower()
                logger.info(f"Evento on-chain capturado: CreatorUnauthorized -> {creator_address}")
                

                if not self.db_manager.existUser(creator_address):
                    logger.warning(
                        f"Usuario desautorizado on-chain {creator_address} ignorado: no existe registro en la DB local."
                    )
                    continue
                
                self.db_manager.unauthorizeUser(creator_address)
                logger.info(f"Proceso de desautorización ejecutado con éxito en DB para: {creator_address}")
                
            except Exception as event_err:
                logger.error(
                    f"Error inesperado al procesar un evento individual CreatorUnauthorized: {str(event_err)}", 
                    exc_info=True
                )

    async def _process_cfp_created(self, from_block: int, to_block: int):
        """
        Filtra y procesa 'event CFPCreated(address creator, bytes32 callId, CFP cfp)'.
        Modifica el objeto localmente con los datos extraídos on-chain y lo persiste.
        """
        event_filter = self.contract.events.CFPCreated.create_filter(from_block=from_block, to_block=to_block)
        
        for event in event_filter.get_all_entries():
            try:
                # Parseo seguro de tipos binarios de solidity a string hexadecimal limpio
                call_id_raw = event.args.callId
                call_id_hex = "0x" + call_id_raw.hex() if isinstance(call_id_raw, bytes) else str(call_id_raw).lower()
                cfp_contract_address = event.args.cfp.lower()
                creator_address = event.args.creator.lower()
                
                logger.info(f"Evento on-chain capturado: CFPCreated ID {call_id_hex} asignado a {cfp_contract_address}")
                
                local_call = self.db_manager.getCall(call_id_hex)
                
                if not local_call:
                    logger.warning(f"Llamado on-chain {call_id_hex} ignorado: no existe registro previo en la DB local.")
                    continue
                
                # Consultamos el closingTime on-chain usando el contractManager
                try:
                    logger.debug(f"Consultando closing time on-chain para el contrato CFP: {cfp_contract_address}")
                    closing_time_timestamp = self.contract_manager.get_cfp_closing_time_by_address(cfp_contract_address)
                except Exception as rpc_err:
                    logger.error(f"No se pudo obtener el closingTime del contrato {cfp_contract_address} vía RPC: {str(rpc_err)}")
                    continue

                local_call.state = CallState.CREATED
                local_call.contractAddress = cfp_contract_address
                local_call.creator = creator_address
                local_call.closingTime = closing_time_timestamp

                self.db_manager.updateExistingCall(local_call)
                
            except Exception as event_err:
                logger.error(f"Error inesperado al procesar un evento individual CFPCreated: {str(event_err)}", exc_info=True)