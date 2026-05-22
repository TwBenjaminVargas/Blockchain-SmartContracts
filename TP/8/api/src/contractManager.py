import os
import json
import logging
from functools import lru_cache
from fastapi import Depends
from web3 import Web3
from web3.providers import HTTPProvider
from .settings import Settings, get_settings
from web3.exceptions import ContractLogicError
import messages as Messages

logger = logging.getLogger(__name__)


class ContractManager:
    
    REVERT_TO_MESSAGE_MAP = {
        "El cierre de la convocatoria no puede estar en el pasado": Messages.INVALID_CLOSING_TIME,
        #"Convocatoria cerrada": Messages.INVALID_CLOSING_TIME,
        "La propuesta ya ha sido registrada": Messages.ALREADY_REGISTERED,
        "Solo el creador puede hacer esta llamada": Messages.UNAUTHORIZED,
        "El llamado ya existe": Messages.ALREADY_CREATED,
        "El llamado no existe": Messages.CALLID_NOT_FOUND,
        "No autorizado": Messages.UNAUTHORIZED,
        "Ya se ha registrado": Messages.ALREADY_AUTHORIZED
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
        abi_path = os.path.join(os.path.dirname(__file__), "abi.json")
        try:
            with open(abi_path, "r", encoding="utf-8") as f:
                abi_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo ABI crucial no encontrado en la ruta: {abi_path}")
            raise

        # Creación del objeto de contrato nativo de web3.py
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi_data)
        logger.info(f"Sistema enlazado con éxito al Smart Contract: {self.contract_address}")
            
    def generate_hex_str_create_message(self, call_id_hex: str, unix_timestamp: int) -> str:
        import struct

        try:
            # Normalizar la dirección del contrato: quitamos el '0x' y pasamos a minúsculas
            contract_hex = self.contract_address.lower().replace("0x", "")

            # Normalizar el callId: removemos el prefijo '0x' y aseguramos minúsculas.
            call_id_clean = call_id_hex.lower().replace("0x", "")

            #Formatear el Timestamp a 32 bytes Hex (64 caracteres) en formato Big Endian
            # Empacamos el entero en 8 bytes (Q = 64 bits) en formato Big Endian (>)
            timestamp_bytes_8 = struct.pack('>Q', unix_timestamp)
            # Rellenamos con 24 bytes vacíos a la izquierda para alcanzar los 32 bytes de la EVM
            timestamp_bytes_32 = b'\x00' * 24 + timestamp_bytes_8
            # Convertimos esos 32 bytes puros a su representación en texto hexadecimal (64 caracteres)
            timestamp_hex = timestamp_bytes_32.hex()

            #Concatenamos los tres bloques de texto y le agregamos el '0x' global al inicio
            hex_message = f"0x{contract_hex}{call_id_clean}{timestamp_hex}"

            logger.debug("Mensaje generado en formato String Hex: %s", hex_message)
            return hex_message

        except Exception as e:
            logger.error(f"Error al estructurar el mensaje en formato String Hex: {str(e)}")
            raise e
    
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
                logger.info(f"Coincidencia encontrada para el revert. Mapeado a: {business_message}")
                return business_message

        #Si no encontramos ninguna palabra clave conocida en el texto de la EVM
        logger.warning(f"No se encontró un mapeo específico para el error de la EVM: '{cle_message}'")
        return Messages.INTERNAL_ERROR
        

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