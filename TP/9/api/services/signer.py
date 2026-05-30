from .settings import Settings, get_settings
from functools import lru_cache
from fastapi import Depends
import logging
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import exceptions.SignerExceptions as signer_exceptions

logger = logging.getLogger(__name__)


class Signer:
    def __init__(self):
        setting = get_settings()
        self.mnemonic = setting.mnemonic_phrase
        self.derivacion_path = setting.derivacion_path
        self.admin_address = setting.admin_address
        logger.debug("Inicializando con frase mnemonica de wallet: %s", self.mnemonic)
        
        # Habilitar HD Wallet en local
        Account.enable_unaudited_hdwallet_features()
        
        logger.debug(f"Derivando cuenta local usando la ruta estándar: {self.derivacion_path}")
        
        #Derivamos la cuenta especificando la ruta
        self._account = Account.from_mnemonic(
            mnemonic=self.mnemonic.strip(),
            account_path=self.derivacion_path
        )
    
        self.address = self._account.address
        logger.debug("Sistema inicializado con la dirección de wallet owner: %s", self.address)
        self.private_key = self._account.key
        
        
    def get_signer_address(self, message_hexstr: str, signature_hex: str) -> str:
        """
        Recupera y valida la dirección de Ethereum asociada a una firma criptográfica.

        Raises:
            signer_exceptions.InvalidInputException: Si los parámetros de entrada no son válidos.
            signer_exceptions.InvalidSignatureException: Si la firma está corrupta o falla el recover.
        """
        if not isinstance(message_hexstr, str) or not isinstance(signature_hex, str):
            logger.error(f"Tipos de datos inválidos en get_signer_address. Message: {type(message_hexstr)}, Signature: {type(signature_hex)}")
            raise signer_exceptions.InvalidInputException("El mensaje y la firma deben ser cadenas de texto.")

        try:
            # Aplica el prefijo estándar \x19Ethereum Signed Message:\n
            signable_message = encode_defunct(hexstr=message_hexstr)
            
            # Recupera la dirección asociada a la firma
            recovered_address = Account.recover_message(
                signable_message, 
                signature=signature_hex
            )
            
            if not recovered_address:
                raise ValueError("La dirección recuperada está vacía.")
            
            return Web3.to_checksum_address(recovered_address)
            
        except (ValueError, TypeError) as crypto_err:
            # Captura longitudes incorrectas, formatos hex inválidos o parámetros mal formados de la firma
            logger.error(f"Firma criptográfica inválida o corrupta: {str(crypto_err)}", exc_info=True)
            raise signer_exceptions.InvalidSignatureException("La firma provista no coincide o su formato es inválido.")
            
        except Exception as e:
            logger.error(f"Fallo inesperado al recuperar el firmante: {str(e)}", exc_info=True)
            raise signer_exceptions.InvalidSignatureException("No se pudo procesar la firma de Ethereum enviada.")  
        
    def check_admin_sign(self, raw_message: str, signature_hex: str) -> bool:
        """
        Verifica si la firma provista corresponde a la clave privada del administrador del sistema.
        Aplica internamente el prefijo estándar de firma de Ethereum.
        """
        try:
            # Aplica el prefijo \x19Ethereum Signed Message:\n e incluye la longitud automáticamente
            signable_message = encode_defunct(hexstr=raw_message)
            
            # Recupera la dirección pública que generó la firma
            recovered_address = Account.recover_message(signable_message, signature=signature_hex)
            
            return recovered_address.lower() == self.admin_address.lower()
        except Exception as e:
            logger.warning(f"Signature recovery failed: {str(e)}")
            return False
    
    def sign_transaction(self, transaction_dict: dict) -> bytes:
        try:
            # Validación temprana de seguridad defensiva
            if not transaction_dict:
                raise signer_exceptions.InvalidTransactionStructureException(
                    "El diccionario de la transacción no puede estar vacío."
                )

            logger.debug(
                "Iniciando el firmado offline de la transacción para el destino: %s", 
                transaction_dict.get("to")
            )

            # Firmar la transacción utilizando la cuenta interna
            signed_tx = self._account.sign_transaction(transaction_dict)

            # Extraemos los bytes del atributo rawTransaction
            raw_tx_bytes = signed_tx.raw_transaction

            logger.debug("Transacción firmada criptográficamente con éxito de forma offline (Bytes listos).")
            return raw_tx_bytes

        except ValueError as ve:
            # Ocurre si faltan campos obligatorios (nonce, gas, to, chainId) o tienen tipos incorrectos
            logger.error("Campos inválidos o faltantes en el diccionario de la transacción: %s", str(ve))
            raise signer_exceptions.InvalidTransactionStructureException(
                "La estructura de la transacción provista es inválida para el firmado."
            )

        except (TypeError, AttributeError) as te:
            # Ocurre si la clave privada de la cuenta interna o el formato del diccionario están corruptos
            logger.error("Error de tipo o configuración en la clave privada o cuenta emisora: %s", str(te))
            raise signer_exceptions.CryptographicSigningException(
                "Error de configuración interna en la clave criptográfica emisora."
            )

        except Exception as e:
            # Cualquier otro fallo crítico inesperado de la librería subyacente
            logger.error("Fallo crítico inesperado al firmar la transacción de forma offline: %s", str(e), exc_info=True)
            raise signer_exceptions.CryptographicSigningException(
                "No se pudo completar el firmado digital de la transacción."
            )

@lru_cache()
def get_signer() -> Signer:
    return Signer()