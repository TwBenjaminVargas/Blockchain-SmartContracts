import logging
from web3 import Web3, HTTPProvider
from services.settings import get_settings
from functools import lru_cache

logger = logging.getLogger(__name__)

class BlockchainConnector:
    def __init__(self, provider_url: str = None):
        settings = get_settings()
        self.provider_path = provider_url or settings.web3_provider_url
        
        if not self.provider_path.lower().startswith(("http://", "https://")):
            raise ValueError(
                f"Proveedor de red no soportado: {self.provider_path}. "
                f"La URL debe comenzar con http:// o https://"
            )

        self.w3 = Web3(HTTPProvider(self.provider_path))
        
        # Validación opcional pero recomendada para asegurar que el nodo responde
        if not self.w3.is_connected():
            raise ConnectionError(f"No se pudo conectar al nodo blockchain en: {self.provider_path}")
            
        self.chain_id = self.w3.eth.chain_id
        logger.debug("BlockchainConnector inicializado en la red con Chain ID: %s", self.chain_id)
        
@lru_cache()
def get_blockchainconnector() -> BlockchainConnector:
    return BlockchainConnector()