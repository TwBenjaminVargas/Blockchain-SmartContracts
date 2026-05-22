from .settings import Settings, get_settings
from functools import lru_cache
from fastapi import Depends
import logging
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

logger = logging.getLogger(__name__)


class Signer:
    def __init__(self, mnemonic: str = "test test test test test test test test test test test junk",
                 derivacion_path: str = "m/44'/60'/0'/0/0"):
        
        logger.debug("Inicializando con frase mnemonica de wallet: %s", mnemonic)
        
        # Habilitar HD Wallet en local
        Account.enable_unaudited_hdwallet_features()
        
        logger.debug(f"Derivando cuenta local usando la ruta estándar: {derivacion_path}")
        
        #Derivamos la cuenta especificando la ruta
        self._account = Account.from_mnemonic(
            mnemonic=mnemonic.strip(),
            account_path=derivacion_path
        )
    
        self.address = self._account.address
        logger.debug("Sistema inicializado con la dirección de wallet: %s", self.address)
        self.private_key = self._account.key
        
        
    def get_signer_address(self, message_hexstr: str, signature_hex: str) -> str:
        try:
            # Aplicar de forma interna el prefijo estándar \x19Ethereum Signed Message:\n84
            signable_message = encode_defunct(hexstr=message_hexstr)
            
            #recuperar la dirección asociada a la firma
            recovered_address = Account.recover_message(
                signable_message, 
                signature=signature_hex
            )
            
            # Chequeo de consistencia: nos aseguramos que devolvió una address
            if not recovered_address:
                raise ValueError("La dirección recuperada no tiene un formato válido de Ethereum.")
            
            checksum_address = Web3.to_checksum_address(recovered_address)
            
            logger.debug(f"Dirección del firmante recuperada con éxito: {checksum_address}")
            return checksum_address
            
        except Exception as e:
            logger.error(f"Fallo crítico al intentar recuperar el firmante: {str(e)}")
            raise ValueError(f"Firma criptográfica inválida o corrupta: {str(e)}")  
        
    def sign_transaction(self, transaction_dict: dict) -> bytes:
        try:
            logger.debug("Iniciando el firmado offline de la transacción para el destino: %s", transaction_dict.get("to"))
            
            #Firmar la transacción utilizando la cuenta interna
            signed_tx = self._account.sign_transaction(transaction_dict)
            
            #Extraemos los bytes del atributo rawTransaction
            raw_tx_bytes = signed_tx.raw_transaction
            
            logger.debug("Transacción firmada criptográficamente con éxito de forma offline (Bytes listos).")
            return raw_tx_bytes
            
        except ValueError as ve:
            logger.error("Error de validación en la estructura de la transacción: %s", str(ve))
            raise ve
        except Exception as e:
            logger.error("Fallo crítico al firmar la transacción: %s", str(e))
            raise e

def get_signer(settings: Settings = Depends(get_settings)) -> Signer:
    return Signer(
        mnemonic=settings.mnemonic_phrase,
        derivacion_path=settings.derivacion_path
    )