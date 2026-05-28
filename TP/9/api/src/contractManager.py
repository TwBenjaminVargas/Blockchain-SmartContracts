import json
import logging
from functools import lru_cache
from fastapi import Depends
from web3 import Web3
from web3.providers import HTTPProvider
from src.settings import Settings, get_settings
from web3.exceptions import ContractLogicError
import messages as Messages
import os

logger = logging.getLogger(__name__)


class ContractManager:
    
    REVERT_TO_MESSAGE_MAP = {
        #?"Convocatoria cerrada": Messages.INVALID_CLOSING_TIME,
        "La propuesta ya ha sido registrada": Messages.ALREADY_REGISTERED,
        "Solo el creador puede hacer esta llamada": Messages.UNAUTHORIZED,
        "El llamado ya existe": Messages.ALREADY_CREATED,
        "El llamado no existe": Messages.CALLID_NOT_FOUND,
        "No autorizado": Messages.UNAUTHORIZED,
    }
    
    
    def __init__(self, provider_url: str, contract_address: str):
        logger.debug("Inicializando ContractManager con proveedor: %s y contrato: %s", provider_url, contract_address)
        
        # Configuración del proveedor HTTP
        provider_path = provider_url.strip()
        if not provider_path.lower().startswith(("http://", "https://")):
            raise ValueError(
                f"Proveedor de red no soportado en ContractManager: {provider_path}. "
                f"La URL debe comenzar con http:// o https://"
            )

        # Instancia única de Web3
        self.w3 = Web3(HTTPProvider(provider_path))
        
        #Formateo seguro de la dirección del contrato (Checksum Address)
        self.contract_address = self.w3.to_checksum_address(contract_address)
        
        #Carga e instanciación del archivo ABI (ubicado en la carpeta 'src/')
        factory_abi_path = os.path.join(os.path.dirname(__file__), "cfp_factory_abi.json")
        try:
            with open(factory_abi_path, "r", encoding="utf-8") as f:
                abi_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo ABI crucial no encontrado en la ruta: {factory_abi_path}")
            raise
        
        cfp_abi_path = os.path.join(os.path.dirname(__file__), "cfp_abi.json")
        try:
            with open(cfp_abi_path, "r", encoding="utf-8") as f:
                self.cfp_abi_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo ABI crucial no encontrado en la ruta: {cfp_abi_path}")
            raise
        logger.debug("cfp_abi.json cargado")

        # Creación del objeto de contrato nativo de web3.py
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi_data)
        logger.debug(f"Sistema enlazado con éxito al Smart Contract: {self.contract_address}")
    
    def generate_call_id(self, title: str, description: str) -> str:
        """
        Genera el callId único calculando keccak256(rlp([title_utf8, description_utf8])).
        """
        try:
            import rlp
            from eth_utils import keccak

            # Convertir los strings de texto a bytes codificados en UTF-8
            title_bytes = title.encode("utf-8")
            description_bytes = description.encode("utf-8")

            # Codificación RLP estándar de la lista conteniendo ambos elementos binarios
            rlp_encoded = rlp.encode([title_bytes, description_bytes])

            # Calcular el hash Keccak256 del bloque RLP completo
            keccak_hash = keccak(rlp_encoded)

            # Retornar el resultado en formato String Hex con prefijo '0x'
            return f"0x{keccak_hash.hex()}"

        except Exception as e:
            logger.error(f"Error al calcular el callId: {str(e)}")
            raise Exception(str(e))
        
    def generate_hex_str_create_message(self, call_id_hex: str) -> str:
        """
        Genera el mensaje base de 62 bytes en formato String Hex (con prefijo 0x).
        Asume que contract_address y call_id_hex ya vienen con el tamaño correcto.
        """
        try:
            # Prefijo fijo de la acción: "createPOST" (10 bytes ASCII)
            prefix_bytes = b"createPOST"

            # Dirección del contrato CFPFactory: string hex a 20 bytes puros
            contract_clean = self.contract_address.lower().replace("0x", "")
            contract_bytes = bytes.fromhex(contract_clean)

            # Identificador callId: string hex a 32 bytes puros
            call_id_clean = call_id_hex.lower().replace("0x", "")
            call_id_bytes = bytes.fromhex(call_id_clean)

            # Concatenación binaria de los tres bloques (10 + 20 + 32 = 62 bytes)
            message_bytes = prefix_bytes + contract_bytes + call_id_bytes

            # Retorna la representación String Hex con prefijo 0x
            return f"0x{message_bytes.hex()}"

        except Exception as e:
            logger.error(f"Error al estructurar el mensaje: {str(e)}")
            raise Exception(str(e))
    
    def generate_hex_str_register_message(self) -> str:
        try:
            # La dirección del contrato ya representa exactamente los 20 bytes (40 caracteres hex).
            # Aseguramos que empiece con '0x' y esté en minúsculas para mantener consistencia.
            contract_hex = self.contract_address.lower()
            if not contract_hex.startswith("0x"):
                contract_hex = f"0x{contract_hex}"

            logger.debug("Mensaje de registro generado en formato String Hex: %s", contract_hex)
            return contract_hex

        except Exception as e:
            logger.error(f"Error al estructurar el mensaje de registro en formato String Hex: {str(e)}")
            raise e

    def create_cfp_for(self, from_address: str,creator_address: str, call_id_hex: str, unix_timestamp: int) -> dict:
        try:
            logger.debug(f"Preparando transacción 'create' para CallId: {call_id_hex}")

            
            # Obtenemos el nonce actual de la wallet emisora directamente del nodo RPC
            nonce = self.w3.eth.get_transaction_count(from_address)

            #Construimos los parámetros base de la transacción on-chain
            tx_params = {
                'from': from_address,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            }

            # Invocamos la función del contrato de Solidity y preparamos el diccionario final
            transaction_dict = self.contract.functions.createFor(
                call_id_hex, 
                unix_timestamp,
                creator_address
            ).build_transaction(tx_params)

            logger.debug("Diccionario de transacción 'createFor' construido exitosamente.")
            return transaction_dict
        
        except ContractLogicError as cle:
            logger.error(f"Error de lógica en el Smart Contract al construir la transacción: {cle.message}")
            raise cle
    
        except Exception as e:
            logger.error(f"Error al construir la transacción create_cfp_for: {str(e)}")
            raise e
        
    #! No podes registar a un usuario con el campo from si no se posee su clave privada
    def register_user(self, user_address: str) -> dict:
        try:
            logger.debug(f"Preparando transacción 'register' para la wallet: {user_address}")

            # Obtenemos el nonce actual de la wallet emisora
            nonce = self.w3.eth.get_transaction_count(user_address)

            # Construimos los parámetros base de la transacción on-chain
            tx_params = {
                'from': user_address,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            }

            # Invocamos la función 'register' de Solidity que no requiere parámetros
            transaction_dict = self.contract.functions.register().build_transaction(tx_params)

            logger.debug("Diccionario de transacción 'register' construido exitosamente.")
            return transaction_dict
        
        except ContractLogicError as cle:
            logger.error(f"Error de lógica en el Smart Contract al construir register: {cle.message}")
            raise cle
        except Exception as e:
            logger.error(f"Error al construir la transacción register_user_tx: {str(e)}")
            raise e
    
    def authorize_user(self, from_address: str, user_address: str) -> dict:
        try:
            logger.debug(f"Preparando transacción 'authorize' para autorizar a: {user_address}")

            # Obtenemos el nonce actual de la wallet del Owner (la API) directamente del nodo RPC
            nonce = self.w3.eth.get_transaction_count(from_address)

            # Construimos los parámetros base de la transacción on-chain
            tx_params = {
                'from': from_address,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            }

            # Invocamos la función 'authorize' de Solidity pasando el parámetro requerido
            transaction_dict = self.contract.functions.authorize(
                user_address
            ).build_transaction(tx_params)

            logger.debug(f"Diccionario de transacción 'authorize' para {user_address} construido exitosamente.")
            return transaction_dict
        
        except ContractLogicError as cle:
            logger.error(f"Error de lógica en el Smart Contract al construir authorize: {cle.message}")
            raise cle
        except Exception as e:
            logger.error(f"Error al construir la transacción authorize_user: {str(e)}")
            raise e
    
    def register_proposal(self, from_address: str, call_id_hex: str, proposal_hex: str) -> dict:
        try:
            logger.debug(
                f"Preparando transacción 'registerProposal' para CallId: {call_id_hex} "
                f"y Proposal: {proposal_hex}"
            )

            nonce = self.w3.eth.get_transaction_count(from_address)

            tx_params = {
                'from': from_address,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id,
                'maxFeePerGas': self.w3.eth.gas_price,
                'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            }

            transaction_dict = self.contract.functions.registerProposal(
                call_id_hex,
                proposal_hex
            ).build_transaction(tx_params)

            logger.debug("Diccionario de transacción 'registerProposal' construido exitosamente.")
            return transaction_dict
        
        except ContractLogicError as cle:
            logger.error(f"Error de lógica en el Smart Contract al construir registerProposal: {cle.message}")
            raise cle
            
        except Exception as e:
            logger.error(f"Error al construir la transacción register_proposal_tx: {str(e)}")
            raise e
    
    def is_address_authorized(self, account_address: str) -> bool:
        try:
            logger.debug(f"Consultando estado de autorización (isAuthorized) para: {account_address}")

            checksum_address = self.w3.to_checksum_address(account_address)

            is_auth = self.contract.functions.isAuthorized(checksum_address).call()

            logger.debug(f"Resultado de isAuthorized para {account_address}: {is_auth}")
            return is_auth

        except Exception as e:
            logger.error(f"Error al consultar isAuthorized para la wallet {account_address}: {str(e)}")
            raise e
    
    def get_call_details(self, call_id_hex: str) -> tuple[str, str]:
        try:
            logger.debug(f"Consultando detalles del llamado para CallId: {call_id_hex}")
            
            call_id_bytes = self.w3.to_bytes(hexstr=call_id_hex)
            creator, cfp_address = self.contract.functions.calls(call_id_bytes).call()
            
            logger.debug(f"Detalles recuperados - Creador: {creator}, CFP: {cfp_address}")
            return creator, cfp_address
            
        except Exception as e:
            logger.error(f"Error al leer el mapeo de llamadas en el contrato: {str(e)}")
            raise e
    
    def execute_transaction(self, raw_tx_bytes: bytes) -> str:
        logger.debug("Transmitiendo transacción firmada al nodo RPC...")
        try:
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx_bytes)

            tx_hash_hex = self.w3.to_hex(tx_hash)
            logger.info(f"Transacción transmitida con éxito al nodo. Hash: {tx_hash_hex}")

            return tx_hash_hex
        except Exception as e:
            logger.error(f"Error al transmitir la transacción al nodo RPC: {str(e)}")
            raise e
    
    def get_transaction_receipt(self, tx_hash_hex: str, timeout: int = 120) -> dict:
        try:
            logger.debug(f"Esperando confirmación del bloque para la transacción: {tx_hash_hex}")

            # Esperamos de forma síncrona a que el nodo mine la transacción y devuelva el recibo
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=timeout)

            logger.info(f"Transacción minada en el bloque {receipt['blockNumber']}")
            return receipt

        except Exception as e:
            logger.error(f"Error o Timeout al intentar verificar la transacción {tx_hash_hex}: {str(e)}")
            raise e
        
    def raise_revert_reason(self, tx_hash_hex: str):
        """
        Simula la transacción fallida en el nodo para extraer 
        el ContractLogicError original y lanzarlo
        """
        try:
            # Buscamos la transacción en la blockchain
            tx = self.w3.eth.get_transaction(tx_hash_hex)

            # Reejecutamos de forma virtual en el mismo bloque
            self.w3.eth.call({
                'to': tx['to'],
                'from': tx['from'],
                'data': tx['input'],
                'value': tx['value']
            }, tx['blockNumber'])

        except ContractLogicError as cle:
            logger.error(f"Revert detectado en el Smart Contract: {cle.message}")
            raise cle

        except Exception as e:
            logger.error(f"Error inesperado al interrogar al nodo: {str(e)}")
            raise e
        
    def get_revert_reason(self, tx_hash_hex):
        try:
            tx = self.w3.eth.get_transaction(tx_hash_hex)

            self.w3.eth.call({
                'to': tx['to'],
                'from': tx['from'],
                'data': tx['input'],
                'value': tx['value']
            }, tx['blockNumber'])

        except ContractLogicError as e:
            logger.error(f"El contrato retorno revert: {e.message}")
            return e.message
        
        except Exception as e:
            logger.error(f"Error inesperado al obtener el motivo de revert: {str(e)}")
            raise e
    
    def map_revert_reason_to_message(self, cle_message: str) -> str:
        if not cle_message:
            return Messages.INTERNAL_ERROR
    
        error_str = str(cle_message).lower()

        logger.debug(f"Procesando error de Solidity original: '{cle_message}'")


        # recorremos el mapa buscando si la palabra clave está CONTENIDA en el error.
        for solidity_revert_keyword, business_message in self.REVERT_TO_MESSAGE_MAP.items():
            if solidity_revert_keyword.lower() in error_str:
                logger.debug(f"Coincidencia encontrada para el revert. Mapeado a: {business_message}")
                return business_message

        #Si no encontramos ninguna palabra clave conocida en el texto de la EVM
        logger.warning(f"No se encontró un mapeo específico para el error de la EVM: '{cle_message}'")
        return Messages.INTERNAL_ERROR
    
    def get_cfp_contract_instance(self, cfp_address: str):
        try:
            logger.debug(f"Generando instancia de contrato CFP para la dirección: {cfp_address}")
            
            checksum_address = self.w3.to_checksum_address(cfp_address)
            cfp_contract = self.w3.eth.contract(
                address=checksum_address,
                abi=self.cfp_abi_data
            )
            
            return cfp_contract
            
        except Exception as e:
            logger.error(f"Error al instanciar el contrato CFP en la dirección {cfp_address}: {str(e)}")
            raise e
    
    def get_cfp_closing_time_by_address(self, cfp_address: str) -> int:
        try:
            logger.debug(f"Consultando variable closingTime en la dirección: {cfp_address}")
            
            cfp_contract = self.get_cfp_contract_instance(cfp_address)
            closing_time_timestamp = cfp_contract.functions.closingTime().call()
            
            logger.debug(f"Timestamp de cierre recuperado: {closing_time_timestamp}")
            return closing_time_timestamp
            
        except Exception as e:
            logger.error(f"Error al obtener el closingTime del contrato CFP en {cfp_address}: {str(e)}")
            raise e
    
    def get_factory_contract_owner(self) -> str:
        try:
            logger.debug("Consultando on-chain al dueño del contrato factoría")
            owner_address = self.contract.functions.owner().call()
            
            logger.debug(f"Dirección del dueño recuperada: {owner_address}")
            return owner_address
            
        except Exception as e:
            logger.error(f"Error al consultar el owner del contrato factoría: {str(e)}")
            raise e
    
    def get_cfp_proposal_data(self, cfp_address: str, proposal_hex: str) -> tuple[str, int, int]:
        try:
            logger.debug(f"Consultando datos de propuesta {proposal_hex} en el contrato CFP {cfp_address}")
            
            cfp_contract = self.get_cfp_contract_instance(cfp_address)
            proposal_bytes = self.w3.to_bytes(hexstr=proposal_hex)
            
            sender, block_number, timestamp = cfp_contract.functions.proposalData(proposal_bytes).call()
            
            logger.debug(f"Datos recuperados - Sender: {sender}, Bloque: {block_number}, Timestamp: {timestamp}")
            return sender, block_number, timestamp
            
        except Exception as e:
            logger.error(f"Error al leer el mapeo proposalData en el contrato CFP: {str(e)}")
            raise e

def get_contract_manager(settings: Settings = Depends(get_settings)) -> ContractManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    Gracias al decorador @lru_cache, la lectura del ABI y la inicialización del 
    proveedor HTTP ocurren UNA SOLA VEZ al recibir la primera petición HTTP de la API.
    """
    return ContractManager(
        provider_url=settings.web3_provider_url,
        contract_address=settings.contract_address
    )