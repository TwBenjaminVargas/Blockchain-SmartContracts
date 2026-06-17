import json
import logging
from functools import lru_cache
from web3 import Web3
from web3.providers import HTTPProvider
from services.settings import get_settings
from web3.types import BlockData
from web3.exceptions import BadFunctionCallOutput, ContractLogicError, Web3Exception, Web3ValidationError,TimeExhausted,TransactionNotFound
import messages as Messages
import os
import exceptions.contractManagerExceptions as cm_exceptions
from eth_utils import keccak, to_bytes, is_hex,to_hex
import rlp
from deprecated import deprecated

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
    
    
    def __init__(self):
        
        settings = get_settings()
        # Configuración del proveedor HTTP
        self.provider_path = settings.web3_provider_url
        if not self.provider_path.lower().startswith(("http://", "https://")):
            raise ValueError(
                f"Proveedor de red no soportado en ContractManager: {self.provider_path}. "
                f"La URL debe comenzar con http:// o https://"
            )

        # Instancia única de Web3
        self.w3 = Web3(HTTPProvider(self.provider_path))
        self.chain_id = self.w3.eth.chain_id
        
        #Formateo seguro de la dirección del contrato (Checksum Address)
        self.contract_address = self.w3.to_checksum_address(settings.contract_address)
        
        
        logger.debug("Inicializando ContractManager con proveedor: %s y contrato: %s", self.provider_path, self.contract_address)
        
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
    
    def get_eip712_domain(self) -> dict:
        """Retorna el dominio EIP-712 unificado usando el chain_id de la instancia."""
        return {
            "name": "CFP API",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": self.contract_address
        }
    
    def generate_call_id(self, title: str, description: str) -> str:
        """
        Genera el callId único calculando keccak256(rlp([title_utf8, description_utf8])).

        Raises:
            InvalidInputTypeException: Si los argumentos de entrada no son strings.
            CryptographicHashingException: Si ocurre un error en la serialización o hashing.
        """
        # Validación preventiva de tipos de datos
        if not isinstance(title, str) or not isinstance(description, str):
            error_msg = f"Tipos de datos inválidos para CallId. Title: {type(title)}, Description: {type(description)}"
            logger.error(error_msg)
            raise cm_exceptions.InvalidInputTypeException("El título y la descripción deben ser strings válidos.")

        try:
            # Convertir los strings de texto a bytes codificados en UTF-8
            title_bytes = title.encode("utf-8")
            description_bytes = description.encode("utf-8")

            # Codificación RLP estándar de la lista
            rlp_encoded = rlp.encode([title_bytes, description_bytes])

            # Keccak256 del bloque RLP completo
            keccak_hash = keccak(rlp_encoded)

            # Retornar el resultado en formato String Hex con prefijo '0x'
            return f"0x{keccak_hash.hex()}"

        except Exception as crypto_err:
            logger.error(f"Fallo crítico en librerías criptográficas al generar CallId: {str(crypto_err)}", exc_info=True)
            raise cm_exceptions.CryptographicHashingException("No se pudo procesar la firma criptográfica de los datos.")
        
    def generate_eip712_create_message(self, call_id_hex: str) -> dict:
        """
        Genera la estructura EIP-712 para la operación CreateRequest.
        """
        if not isinstance(call_id_hex, str):
            raise cm_exceptions.InvalidInputTypeException("El callId debe ser una cadena de texto válida.")

        types = {
            "CreateRequest": [
                {"name": "operation", "type": "string"},
                {"name": "contract", "type": "address"},
                {"name": "callId", "type": "bytes32"}
            ]
        }

        message = {
            "operation": "create",
            "contract": self.contract_address,
            "callId": Web3.to_bytes(hexstr=call_id_hex)
        }

        return {
            "domain": self.get_eip712_domain(),
            "types": types,
            "primaryType": "CreateRequest",
            "message": message
        }

    def generate_eip712_register_message(self, nonce: int, name: str, is_update: bool = False) -> dict:
        """
        Genera la estructura EIP-712 para RegisterRequest (Registro inicial o Actualización).
        """
        if not isinstance(name, str):
            raise cm_exceptions.InvalidInputTypeException("El nombre debe ser un string válido.")
        if not isinstance(nonce, int) or nonce < 0:
            raise cm_exceptions.InvalidInputTypeException("El nonce debe ser un entero no negativo.")

        types = {
            "RegisterRequest": [
                {"name": "operation", "type": "string"},
                {"name": "contract", "type": "address"},
                {"name": "nonce", "type": "uint256"},
                {"name": "name", "type": "string"}
            ]
        }

        message = {
            "operation": "update" if is_update else "register",
            "contract": self.contract_address,
            "nonce": nonce,
            "name": name
        }

        return {
            "domain": self.get_eip712_domain(),
            "types": types,
            "primaryType": "RegisterRequest",
            "message": message
        }

    def generate_eip712_admin_action_message(self, admin_nonce: int, target_address: str, is_authorize: bool = True) -> dict:
        """
        Genera la structure EIP-712 para AdminActionRequest (Authorize o Unauthorize).
        """
        if not isinstance(admin_nonce, int) or admin_nonce < 0:
            raise cm_exceptions.InvalidInputTypeException("El nonce del administrador debe ser un entero no negativo.")
        
        types = {
            "AdminActionRequest": [
                {"name": "operation", "type": "string"},
                {"name": "contract", "type": "address"},
                {"name": "nonce", "type": "uint256"},
                {"name": "target", "type": "address"}
            ]
        }

        message = {
            "operation": "authorize" if is_authorize else "unauthorize",
            "contract": self.contract_address,
            "nonce": admin_nonce,
            "target": Web3.to_checksum_address(target_address)
        }

        return {
            "domain": self.get_eip712_domain(),
            "types": types,
            "primaryType": "AdminActionRequest",
            "message": message
        }


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
        """
        Construye y retorna el diccionario de la transacción 'authorize' listo para ser firmado.
        """
        try:
            logger.debug(f"Preparando parámetros para transacción 'authorize' a: {user_address}")
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_target = Web3.to_checksum_address(user_address)

            try:
                # Usamos la dirección con checksum para consultar el nodo
                nonce = self.w3.eth.get_transaction_count(checksum_from)
                chain_id = self.w3.eth.chain_id
                gas_price = self.w3.eth.gas_price
                max_priority_fee = self.w3.eth.max_priority_fee
            except Web3Exception as rpc_err:
                logger.error(f"Fallo de conexión RPC al consultar parámetros de red: {str(rpc_err)}")
                raise cm_exceptions.NodeRPCException(
                    "Error al conectar con el proveedor RPC de Ethereum para consultar el nonce o tarifas de gas."
                )

            tx_params = {
                'from': checksum_from, # Con checksum
                'nonce': nonce,
                'chainId': chain_id,
                'maxFeePerGas': gas_price,
                'maxPriorityFeePerGas': max_priority_fee,
            }

            try:
                transaction_dict = self.contract.functions.authorize(
                    checksum_target
                ).build_transaction(tx_params)

                logger.debug(f"Diccionario de transacción generado para {user_address}.")
                return transaction_dict

            except ContractLogicError as cle:
                error_msg = str(cle).replace("execution reverted:", "").strip()
                logger.warning(f"El Smart Contract revirtió la simulación de 'authorize': {error_msg}")
                raise cm_exceptions.BlockchainContractLogicException(
                    f"La validación del Smart Contract falló. Razón: {error_msg}"
                )
            except Web3Exception as tx_err:
                logger.error(f"Error de infraestructura al compilar parámetros de la tx: {str(tx_err)}")
                raise cm_exceptions.BlockchainTransactionException(
                    f"No se pudo estructurar la transacción debido a un problema de infraestructura: {str(tx_err)}"
                )

        except (cm_exceptions.NodeRPCException, cm_exceptions.BlockchainContractLogicException, cm_exceptions.BlockchainTransactionException):
            raise

        except Exception as e:
            logger.error(f"Fallo inesperado fuera del flujo Web3 en authorize_user: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainTransactionException(f"Error interno fatal al preparar la autorización: {str(e)}")
    
    def unauthorize_user(self, from_address: str, user_address: str) -> dict:
        """
        Construye y retorna el diccionario de la transacción 'unauthorize' listo para ser firmado.
        """
        try:
            logger.debug(f"Preparando parámetros para transacción 'unauthorize' a: {user_address}")
            checksum_from = Web3.to_checksum_address(from_address)
            checksum_target = Web3.to_checksum_address(user_address)

            try:
                # Usamos la dirección con checksum para consultar el nodo
                nonce = self.w3.eth.get_transaction_count(checksum_from)
                chain_id = self.w3.eth.chain_id
                gas_price = self.w3.eth.gas_price
                max_priority_fee = self.w3.eth.max_priority_fee
            except Web3Exception as rpc_err:
                logger.error(f"Fallo de conexión RPC al consultar parámetros de red: {str(rpc_err)}")
                raise cm_exceptions.NodeRPCException(
                    "Error al conectar con el proveedor RPC de Ethereum para consultar el nonce o tarifas de gas."
                )

            tx_params = {
                'from': checksum_from, # Con checksum
                'nonce': nonce,
                'chainId': chain_id,
                'maxFeePerGas': gas_price,
                'maxPriorityFeePerGas': max_priority_fee,
            }

            try:
                transaction_dict = self.contract.functions.unauthorize(
                    checksum_target
                ).build_transaction(tx_params)

                logger.debug(f"Diccionario de transacción generado para {user_address}.")
                return transaction_dict

            except ContractLogicError as cle:
                error_msg = str(cle).replace("execution reverted:", "").strip()
                logger.warning(f"El Smart Contract revirtió la simulación de 'unauthorize': {error_msg}")
                raise cm_exceptions.BlockchainContractLogicException(
                    f"La validación del Smart Contract falló. Razón: {error_msg}"
                )
            except Web3Exception as tx_err:
                logger.error(f"Error de infraestructura al compilar parámetros de la tx: {str(tx_err)}")
                raise cm_exceptions.BlockchainTransactionException(
                    f"No se pudo estructurar la transacción debido a un problema de infraestructura: {str(tx_err)}"
                )

        except (cm_exceptions.NodeRPCException, cm_exceptions.BlockchainContractLogicException, cm_exceptions.BlockchainTransactionException):
            raise

        except Exception as e:
            logger.error(f"Fallo inesperado fuera del flujo Web3 en authorize_user: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainTransactionException(f"Error interno fatal al preparar la desautorización: {str(e)}")
    
    def register_proposal(self, from_address: str, call_id_hex: str, proposal_hex: str) -> dict:
        try:
            logger.debug(
                f"Preparando transacción 'registerProposal' para CallId: {call_id_hex} "
                f"y Proposal: {proposal_hex} desde {from_address}"
            )

            #Parámetros de red obtenidos de forma segura
            try:
                nonce = self.w3.eth.get_transaction_count(from_address)
                chain_id = self.w3.eth.chain_id
                gas_price = self.w3.eth.gas_price
                priority_fee = self.w3.eth.max_priority_fee
            except Exception as net_err:
                logger.error(f"No se pudieron obtener los parámetros de red del nodo RPC: {str(net_err)}")
                raise cm_exceptions.BlockchainTransactionException("Error de comunicación con el nodo Blockchain.")

            tx_params = {
                'from': from_address,
                'nonce': nonce,
                'chainId': chain_id,
                'maxFeePerGas': gas_price,
                'maxPriorityFeePerGas': priority_fee,
            }

            #Construcción y estimación de la transacción
            transaction_dict = self.contract.functions.registerProposal(
                call_id_hex,
                proposal_hex
            ).build_transaction(tx_params)

            logger.debug("Diccionario de transacción 'registerProposal' construido exitosamente.")
            return transaction_dict

        except ContractLogicError as cle:
            # Captura los revert() y require() del Smart Contract (ej: "Call is not active")
            error_msg = getattr(cle, "message", str(cle))
            logger.warning(f"Lógica del Smart Contract rechazó la transacción registerProposal: {error_msg}")
            raise cm_exceptions.BlockchainContractLogicException(f"Revert en Smart Contract: {error_msg}")

        except (Web3ValidationError, ValueError) as val_err:
            # Captura errores si las direcciones o hashes hex pasados están mal formados para Web3
            logger.error(f"Argumentos inválidos pasados a la función del contrato: {str(val_err)}")
            raise cm_exceptions.BlockchainTransactionException("Los datos criptográficos provistos tienen un formato inválido.")

        except Exception as e:
            # Captura fondos insuficientes (insufficient funds), nonces viejos, o caídas del nodo
            logger.error(f"Error crítico al construir la transacción register_proposal_tx: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainTransactionException("No se pudo construir la transacción debido a un problema en el nodo emisor.")
    
    def is_address_registered(self, account_address: str) -> bool:
        """
        Consulta al contrato Factory si una direccion se encuentra registrada.
        """
        try:
            return self.contract.functions.isRegistered(
                Web3.to_checksum_address(account_address)
            ).call()
        except Exception as e:
            logger.error(f"Error executing isRegistered on-chain for {account_address}: {str(e)}")
            raise cm_exceptions.BlockchainReadException(
                "No se pudo verificar el estado de registro en la blockchain."
            )
    
    def is_address_authorized(self, account_address: str) -> bool:
        """
        Consultando el estado de autorización (isAuthorized) en el Smart Contract.

        Raises:
            cm_exceptions.InvalidInputTypeException: Si la dirección recibida no es un string o está malformada.
            cm_exceptions.NodeRPCException: Si ocurre un error de conectividad o ejecución en el nodo RPC.
        """
        if not isinstance(account_address, str):
            logger.error(f"Tipo de dato inválido para account_address: {type(account_address)}")
            raise cm_exceptions.InvalidInputTypeException("La dirección de la cuenta debe ser una cadena de texto válida.")

        try:
            checksum_address = self.w3.to_checksum_address(account_address)
        except ValueError as addr_err:
            logger.error(f"La dirección provista no cumple con el formato hexadecimal/checksum de Ethereum: {account_address}")
            raise cm_exceptions.InvalidInputTypeException("La dirección provista no es una dirección de Ethereum válida.")

        try:
            is_auth = self.contract.functions.isAuthorized(checksum_address).call()
            logger.debug(f"Resultado de isAuthorized para {checksum_address}: {is_auth}")
            return is_auth

        except Exception as rpc_err:
            logger.error(f"Error al consultar el estado de autorización en el nodo para la wallet {checksum_address}: {str(rpc_err)}", exc_info=True)
            raise cm_exceptions.NodeRPCException("No se pudo obtener una respuesta del nodo de red para validar la autorización.")
    
    def get_call_details(self, call_id_hex: str) -> tuple[str, str]:
        try:
            # Validación defensiva del formato del callId
            if not call_id_hex or not call_id_hex.startswith("0x"):
                raise cm_exceptions.BlockchainReadException("El formato del identificador del llamado es inválido.")
    
            logger.debug(f"Consultando detalles del llamado para CallId: {call_id_hex}")
            
            call_id_bytes = self.w3.to_bytes(hexstr=call_id_hex)
            creator, cfp_address = self.contract.functions.calls(call_id_bytes).call()
            
            if creator == "0x0000000000000000000000000000000000000000":
                logger.warning(f"El llamado {call_id_hex} se consultó pero no existe en el Smart Contract.")
                return None, None
            
            logger.debug(f"Detalles recuperados - Creador: {creator}, CFP: {cfp_address}")
            return creator, cfp_address
            
        except (BadFunctionCallOutput, Web3ValidationError) as contract_err:
            logger.error(f"Error de interfaz al consultar la factoría. Posible ABI desactualizado o contrato corrupto: {str(contract_err)}")
            raise cm_exceptions.InvalidContractAddressException("La interfaz del contrato de la factoría devolvió una salida inesperada.")
            
        except Exception as e:
            logger.error(f"Error crítico al leer el mapeo de llamadas en el contrato: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException("No se pudieron recuperar los detalles del llamado desde la red blockchain.")
        
    def execute_transaction(self, raw_tx_bytes: bytes) -> str:
        # Validación defensiva inicial
        if not raw_tx_bytes:
            raise cm_exceptions.BlockchainBroadcastException(
                "Los bytes de la transacción firmada no pueden estar vacíos."
            )

        logger.debug("Transmitiendo transacción firmada al nodo RPC...")
        try:
            # Transmisión a la red
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx_bytes)

            tx_hash_hex = self.w3.to_hex(tx_hash)
            logger.info(f"Transacción transmitida con éxito al nodo. Hash: {tx_hash_hex}")

            return tx_hash_hex

        except ValueError as ve:
            # Los nodos EVM (Geth, Hardhat, Anvil) suelen devolver los errores de mempool como ValueErrors con un JSON interno
            error_msg = str(ve).lower()
            logger.error(f"El nodo RPC rechazó la transacción cruda debido a reglas de mempool: {str(ve)}")

            if "insufficient funds" in error_msg:
                raise cm_exceptions.UnderfundedWalletException(
                    "La billetera del servidor no posee fondos suficientes para costear el Gas de la transacción."
                )
            elif "nonce too low" in error_msg or "nonce" in error_msg:
                raise cm_exceptions.NonceCollisionException(
                    "Colisión de Nonce detectada. La transacción está desfasada con el estado actual de la red."
                )
            else:
                raise cm_exceptions.BlockchainBroadcastException(
                    f"La transacción fue rechazada por el nodo: {str(ve)}"
                )

        except Exception as e:
            # Captura errores de conectividad de red (HTTPError, timeout del nodo RPC, etc.)
            logger.error(f"Error crítico de conectividad o infraestructura al transmitir al nodo RPC: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainBroadcastException(
                "No se pudo establecer comunicación con la red Blockchain para transmitir la transacción."
            )
    
    def get_transaction_receipt(self, tx_hash_hex: str, timeout: int = 120) -> dict:
        # Validación defensiva del formato del hash
        if not tx_hash_hex or not tx_hash_hex.startswith("0x"):
            raise cm_exceptions.TransactionNotFoundException(
                "El formato del hash de la transacción es inválido."
            )

        logger.debug(f"Esperando confirmación del bloque para la transacción: {tx_hash_hex} (Timeout: {timeout}s)")
        try:
            # Esperamos a que el nodo mine la transacción
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=timeout)

            if receipt.get("status") == 0:
                revert_reason = self._extract_revert_reason(tx_hash_hex)
                logger.warning(f"Transacción {tx_hash_hex} falló. Razón del Smart Contract: {revert_reason}")
                # Lanzamos la excepción de dominio llevando el mensaje original de Solidity
                raise cm_exceptions.BlockchainContractLogicException(revert_reason)

            logger.info(f"Transacción minada con éxito en el bloque {receipt['blockNumber']}")
            return dict(receipt)

        except TimeExhausted as te: 
            # La transacción sigue viva en el mempool, pero el servidor no puede esperar más
            logger.warning(f"Tiempo de espera agotado ({timeout}s) esperando el recibo de {tx_hash_hex}: {str(te)}")
            raise cm_exceptions.BlockchainTimeoutException(
                "La transacción está tardando demasiado en minarse debido a la congestión de la red."
            )

        except TransactionNotFound as tnf:
            # El nodo no conoce este hash
            logger.error(f"El hash de transacción {tx_hash_hex} no fue encontrado en el nodo: {str(tnf)}")
            raise cm_exceptions.TransactionNotFoundException(
                "La transacción especificada no existe o fue descartada por el mempool."
            )

        except cm_exceptions.TransactionRevertedException:
            # Volvemos a lanzar nuestra propia excepción de revert detectada en el bloque IF de arriba
            raise

        except Exception as e:
            # Errores de red o pérdida de conexión con el nodo RPC en medio de la espera
            logger.error(f"Fallo crítico de infraestructura al verificar el recibo {tx_hash_hex}: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainBroadcastException(
                "Se perdió la conexión con el nodo RPC mientras se esperaba la confirmación del bloque."
            )
    
    def _extract_revert_reason(self, tx_hash_hex: str) -> str:
        """
        Simula la transacción fallida de forma interna para extraer el texto del revert.
        """
        try:
            tx = self.w3.eth.get_transaction(tx_hash_hex)
            # Reejecutamos de forma virtual en el mismo bloque
            self.w3.eth.call({
                'to': tx['to'],
                'from': tx['from'],
                'data': tx['input'],
                'value': tx['value']
            }, tx['blockNumber'])

            return "Unknown revert reason (simulation succeeded)"

        except ContractLogicError as cle:
            # Extraemos el mensaje limpio (ej: "Call is not active" o "Already registered")
            return getattr(cle, "message", str(cle))
        except Exception as e:
            logger.error(f"No se pudo simular el revert para {tx_hash_hex}: {str(e)}")
            return "Execution reverted without reason"

    def get_pending_registrations(self,owner_address: str) -> list[str]:
        """
        Lee el listado completo de registraciones pendientes desde el contrato inteligente.
        Requiere ejecutarse desde la dirección del owner
        """
        try:
            # onlyOwner()
            call_options = {'from': owner_address} 
            
            count = self.contract.functions.pendingCount().call(call_options)
            
            pending_addresses = []
            
            # uno por uno según su índice
            for i in range(count):
                address = self.contract.functions.getPending(i).call(call_options)
                pending_addresses.append(address)
                
            return pending_addresses
            
        except Exception as e:
            logger.error(f"Error al leer pendingList del contrato: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException("No se pudo obtener el listado de pendientes on-chain.")

    def get_created_by_count(self, creator_address: str) -> int:
        """
        Llama a la función view 'createdByCount' del contrato para obtener
        la cantidad de llamados creados por una dirección específica.
        """
        try:
            checksum_address = Web3.to_checksum_address(creator_address)
            count = self.contract.functions.createdByCount(checksum_address).call()
            return int(count)
            
        except Exception as e:
            logger.error(f"Error al obtener createdByCount para {creator_address}: {e}")
            raise cm_exceptions.BlockchainReadException(
                "No se pudo recuperar la cantidad de llamados creados por la dirección desde la blockchain."
            )
            
    @deprecated(version='2.0.0', reason="Migrado al nuevo metodo de manejo de receipt")
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
    
    def get_block_data_by_number(self, block_number: int) -> BlockData:
        """
        Consulta on-chain y recupera toda la información técnica de un bloque específico.

        :param block_number: Número de bloque a consultar.
        :return: Objeto BlockData (un diccionario con los datos nativos de la EVM).
        """
        try:
            if block_number is None or block_number < 0:
                logger.error(f"Se intentó consultar un número de bloque inválido: {block_number}")
                raise cm_exceptions.BlockchainReadException(
                    "El número de bloque provisto no es válido."
                )

            logger.debug(f"Consultando metadatos en el nodo RPC para el bloque número: {block_number}")


            # El parámetro full_transactions=False hace que solo devuelva los hashes de las TXs, 
            # optimizando la velocidad y el consumo de memoria.
            block_data = self.w3.eth.get_block(block_number, full_transactions=False)

            if not block_data:
                logger.warning(f"El bloque {block_number} fue consultado pero el nodo devolvió un objeto vacío.")
                raise cm_exceptions.BlockchainReadException(
                    f"El bloque número {block_number} no pudo ser encontrado en la cadena actual."
                )

            logger.debug(f"Datos de bloque {block_number} recuperados. Timestamp Unix: {block_data.get('timestamp')}")
            return block_data

        except Exception as e:
            # Captura errores de infraestructura (Nodo RPC caído, timeouts de red, etc.)
            logger.error(f"Error crítico de infraestructura al obtener el bloque {block_number}: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException(
                "No se pudieron recuperar los datos del bloque desde la red blockchain."
            )
    
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
            if not cfp_address or not self.w3.is_address(cfp_address):
                logger.error(f"Formato de dirección Ethereum inválido: '{cfp_address}'")
                raise cm_exceptions.InvalidContractAddressException(
                    "La dirección provista para el contrato CFP no es una dirección válida."
                )

            #Instanciación y llamada view on-chain
            cfp_contract = self.get_cfp_contract_instance(cfp_address)
            closing_time_timestamp = cfp_contract.functions.closingTime().call()

            logger.debug(f"Timestamp de cierre recuperado: {closing_time_timestamp}")
            return closing_time_timestamp

        except (BadFunctionCallOutput, Web3ValidationError) as contract_err:
            # Se ejecuta si la dirección no tiene código desplegado (EOA) o si el contrato no implementa 'closingTime'
            logger.error(
                f"La dirección {cfp_address} no responde a la interfaz CFP esperada (Falta variable closingTime): {str(contract_err)}"
            )
            raise cm_exceptions.InvalidContractAddressException(
                "La dirección provista no corresponde a un Smart Contract de propuesta activo o compatible."
            )

        except Exception as e:
            # Captura errores de infraestructura (Nodo RPC caído, timeouts de red, etc.)
            logger.error(f"Error crítico de infraestructura al obtener el closingTime en {cfp_address}: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException(
                "No se pudo recuperar la fecha de cierre del llamado desde la red blockchain."
            )
    
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
            if not self.w3.is_address(cfp_address):
                logger.error(f"Dirección de contrato CFP con formato inválido provista: {cfp_address}")
                raise cm_exceptions.InvalidContractAddressException("La dirección provista para el contrato CFP no es una dirección Ethereum válida.")

            if not proposal_hex or not proposal_hex.startswith("0x"):
                raise cm_exceptions.BlockchainReadException("El formato del identificador de la propuesta es inválido.")

            logger.debug(f"Consultando datos de propuesta {proposal_hex} en el contrato CFP {cfp_address}")

            cfp_contract = self.get_cfp_contract_instance(cfp_address)
            proposal_bytes = self.w3.to_bytes(hexstr=proposal_hex)

            sender, block_number, timestamp = cfp_contract.functions.proposalData(proposal_bytes).call()

            logger.debug(f"Datos recuperados - Sender: {sender}, Bloque: {block_number}, Timestamp: {timestamp}")
            return sender, block_number, timestamp

        except BadFunctionCallOutput:
            # Se ejecuta si la dirección apunta a un contrato que NO implementa la función 'proposalData' (EOA o contrato erróneo)
            logger.error(f"La dirección {cfp_address} no corresponde a un contrato CFP válido o no implementa 'proposalData'.")
            raise cm_exceptions.InvalidContractAddressException("La dirección provista no corresponde a un Smart Contract de propuesta activo.")

        except Exception as e:
            logger.error(f"Error de infraestructura al leer el mapeo proposalData en el contrato CFP: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException("No se pudieron recuperar los datos de la propuesta desde el contrato on-chain.")
        
    def generate_merkle_tree(self, call_id: str, title: str, description: str, files: list[str]) -> tuple[str, dict[str, list[str]], str, str]:
        """
        Calcula la raíz de Merkle (proposalId) y las pruebas individuales para cada hoja.
        """
        try:
            title_bytes = keccak(title.encode('utf-8'))
            desc_bytes = keccak(description.encode('utf-8'))
            call_bytes = bytes.fromhex(call_id.replace("0x", ""))

            title_hash = f"0x{title_bytes.hex()}".lower()
            desc_hash = f"0x{desc_bytes.hex()}".lower()

            try:
                file_leaves = [bytes.fromhex(f.replace("0x", "")) for f in files]
            except ValueError as hex_err:
                logger.error(f"Error de formato hexadecimal al procesar elementos del árbol Merkle: {str(hex_err)}")
                raise cm_exceptions.InvalidInputTypeException("Formato hexadecimal inválido en los hashes de entrada.")

            raw_leaves = sorted([call_bytes, title_bytes, desc_bytes] + file_leaves)
            n = len(raw_leaves)

            # Construcción del Árbol (Arreglo lineal de 2n - 1)
            tree = [bytes(0)] * (2 * n - 1)

            # Colocar las hojas al final del arreglo
            for i in range(n):
                tree[2 * n - 2 - i] = raw_leaves[i]

            # Calcular los nodos internos combinando los hijos correspondientes
            for i in range(n - 2, -1, -1):
                left, right = tree[2 * i + 1], tree[2 * i + 2]
                # Lógica OpenZeppelin standard pairing
                combined = min(left, right) + max(left, right)
                tree[i] = keccak(combined)

            proposal_id_root = f"0x{tree[0].hex()}".lower()
            logger.debug(f"Raíz de Merkle calculada: {proposal_id_root}")

            # Generación de Pruebas (Proofs) navegando de forma inversa desde cada hoja hacia la raíz
            proofs = {}
            for i in range(n):
                leaf_str = f"0x{raw_leaves[i].hex()}".lower()
                proof_hashes = []

                # El índice inicial de la hoja actual dentro del arreglo `tree`
                current_idx = 2 * n - 2 - i

                # Subir por el árbol hasta alcanzar la raíz (índice 0)
                while current_idx > 0:
                    if current_idx % 2 == 0:
                        # El nodo actual es un hijo derecho, su hermano es el izquierdo (current_idx - 1)
                        sibling = tree[current_idx - 1]
                        parent_idx = (current_idx - 2) // 2
                    else:
                        # El nodo actual es un hijo izquierdo, su hermano es el derecho (current_idx + 1)
                        sibling = tree[current_idx + 1]
                        parent_idx = (current_idx - 1) // 2

                    proof_hashes.append(f"0x{sibling.hex()}".lower())
                    current_idx = parent_idx

                proofs[leaf_str] = proof_hashes
                logger.debug(f"Pruebas generadas {proofs}")

            return proposal_id_root, proofs, title_hash, desc_hash

        except Exception as e:
            if isinstance(e, cm_exceptions.InvalidInputTypeException):
                raise e
            logger.error(f"Fallo criptográfico inesperado al calcular la raíz Merkle: {str(e)}")
            raise cm_exceptions.CryptographicHashingException("Error interno en el procesamiento criptográfico del árbol.")
                
    def verify_merkle_proof(self, proposal_id: str, leaf: str, proof: list[str]) -> bool:
        """
        Verifica de forma local si una hoja pertenece al árbol de Merkle usando el algoritmo de OpenZeppelin.
        Cada nodo interno se calcula como keccak256(min(a, b) ++ max(a, b)).
        """
        try:
            current_hash = to_bytes(hexstr=leaf)
            
            for proof_element in proof:
                element_bytes = to_bytes(hexstr=proof_element)
                
                # Ordenamiento lexicográfico estricto byte a byte
                if current_hash <= element_bytes:
                    combined = current_hash + element_bytes
                else:
                    combined = element_bytes + current_hash
                    
                current_hash = keccak(combined)
            
            computed_root = to_hex(current_hash).lower()
            return computed_root == proposal_id.lower()
            
        except Exception as e:
            logger.error(f"Fallo crítico durante la verificación de la prueba Merkle: {str(e)}")
            raise cm_exceptions.CryptographicHashingException("No se pudo procesar la verificación criptográfica de la prueba.")

    def get_cfp_creators(self) -> list[str]:
        """
        Obtiene el listado completo de direcciones de creadores desde el contrato.
        """
        try:
            creators = self.contract.functions.getCreators().call()
            logger.debug(f"Listado de creadores recuperado del contrato: {creators}")
            return creators
        except Exception as e:
            logger.error(f"Error al leer el listado de creadores en el contrato: {str(e)}")
            raise cm_exceptions.BlockchainReadException("No se pudo recuperar el listado de creadores")

    def get_creator_call_ids(self, creator_address: str) -> list[bytes]:
        """
        Obtiene iterativamente la lista de callIds (bytes32) creados por un usuario.
        """
        try:
            # Aseguramos el formato Checksum para Web3
            addr = Web3.to_checksum_address(creator_address)
            
            # Consultamos la cantidad de llamados del creador
            count = self.contract.functions.createdByCount(addr).call()
            
            call_ids = []
            for i in range(count):
                call_id = self.contract.functions.createdBy(addr, i).call()
                call_ids.append(to_hex(call_id).lower())
                
            return call_ids
        except Exception as e:
            logger.error(f"Error al leer llamados creados por {creator_address}: {str(e)}")
            raise cm_exceptions.BlockchainReadException("No se pudieron obtener los llamados del creador desde la red.")

    def get_cfp_details_batch(self, call_ids: list[str]) -> list[dict]:
        """
        Consulta el mapping 'calls' para un listado de call_ids y recupera
        los detalles (contractAddress y closingTime) desde el contrato CFP instanciado.
        """
        
        details = []
        try:
            for call_id in call_ids:
                # calls(callId) retorna una tupla (address creator, address cfp)
                creator_address, cfp_address = self.contract.functions.calls(to_bytes(hexstr=call_id)).call()
                
                # Verificamos que el contrato CFP se haya instanciado realmente
                if cfp_address != "0x0000000000000000000000000000000000000000":
                    cfp_contract = self.contract.w3.eth.contract(address=cfp_address, abi=self.cfp_abi_data)
                    closing_time = cfp_contract.functions.closingTime().call()
                    
                    details.append({
                        "callId": call_id.lower(),
                        "contractAddress": cfp_address,
                        "closingTime": closing_time
                    })
                    
            return details
        except Exception as e:
            logger.error(f"Error al obtener los detalles batch de los CFPs: {str(e)}")
            raise cm_exceptions.BlockchainReadException("No se pudieron consultar los detalles de los CFPs externos.")
    
    def get_all_global_call_ids(self) -> list[str]:
        """
        Consulta on-chain y retorna el listado completo de Call IDs (bytes32)
        almacenados en el array global de la factoría.
        
        :return: Lista de strings hexadecimales con prefijo '0x' en lowercase.
        """
        try:
            logger.debug("Consultando catálogo global de Call IDs en la blockchain...")
            
            # Invocamos la función view del contrato
            raw_call_ids_bytes = self.contract.functions.getGlobalCalls().call()
            
            # Convertimos cada elemento de bytes a un string hexadecimal normalizado
            global_call_ids_hex = [to_hex(cid_bytes).lower() for cid_bytes in raw_call_ids_bytes]
            
            logger.debug(f"Se recuperaron {len(global_call_ids_hex)} Call IDs globales desde la blockchain.")
            return global_call_ids_hex
            
        except Exception as e:
            logger.error(f"Error crítico al leer getGlobalCalls en el contrato factoría: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException(
                "No se pudo recuperar el listado global de convocatorias desde la red blockchain."
            )
        
    def get_cfp_full_details_batch(self, call_ids: list[str]) -> list[dict]:
        """
        Consulta de forma iterativa el mapping 'calls' de la factoría para un listado de 
        Call IDs. Obtiene el creador, la dirección del contrato CFP y consulta a cada 
        contrato CFP su 'closingTime'.
        
        :param call_ids: Lista de strings hexadecimales con los IDs de los llamados.
        :return: Lista de diccionarios con el detalle completo de cada convocatoria.
        """
        full_details = []
        try:
            logger.debug(f"Iniciando consulta iterativa de detalles para {len(call_ids)} llamados...")
            
            for call_id in call_ids:
                # Convertimos el string hex a bytes para pegarle al mapping de Solidity
                call_id_bytes = to_bytes(hexstr=call_id)
                
                # calls(bytes32) retorna la estructura CallForProposals: (address creator, address cfp)
                creator_address, cfp_address = self.contract.functions.calls(call_id_bytes).call()
                
                # Verificamos si el llamado realmente existe (si no existe, el address es 0x0)
                if cfp_address != "0x0000000000000000000000000000000000000000":
                    try:
                        # Instanciamos el contrato CFP hijo usando su dirección y el ABI correspondiente
                        cfp_contract = self.w3.eth.contract(
                            address=self.w3.to_checksum_address(cfp_address), 
                            abi=self.cfp_abi_data
                        )
                        # Consultamos el tiempo de cierre al contrato CFP
                        closing_time = cfp_contract.functions.closingTime().call()
                        
                        full_details.append({
                            "callId": call_id.lower(),
                            "address": cfp_address,
                            "creator": creator_address,
                            "closingTime": closing_time
                        })
                    except Exception as cfp_err:
                        # Si un contrato CFP falla individualmente, lo logueamos pero seguimos con los demás
                        logger.warning(f"No se pudo leer el closingTime del CFP en {cfp_address}: {str(cfp_err)}")
                        continue
                        
            logger.debug(f"Detalles recuperados exitosamente para {len(full_details)} llamados activos.")
            return full_details
            
        except Exception as e:
            logger.error(f"Error crítico en el procesamiento por lote de detalles de CFPs: {str(e)}", exc_info=True)
            raise cm_exceptions.BlockchainReadException(
                "No se pudieron recuperar los detalles completos de las convocatorias desde la blockchain."
            )
            
    def hash_file_contents(self, file_bytes: bytes) -> str:
        """
        Calcula el hash keccak256 de los bytes de un archivo.
        """
        if not file_bytes:
            return "0x" + "0" * 64
        return to_hex(keccak(primitive=file_bytes))
            
@lru_cache()
def get_contract_manager() -> ContractManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    Gracias al decorador @lru_cache, la lectura del ABI y la inicialización del 
    proveedor HTTP ocurren UNA SOLA VEZ al recibir la primera petición HTTP de la API.
    """
    return ContractManager()