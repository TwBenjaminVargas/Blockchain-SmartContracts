import logging
import json
import os
from services.settings import get_settings
from services.BlockchainConector import get_blockchainconnector
from functools import lru_cache


logger = logging.getLogger(__name__)

class ENSManager:
    def __init__(self, web3_instance):
        
        settings = get_settings()
        connector = get_blockchainconnector()
        self.w3 = connector.w3
        
        self.registry_address = settings.registry_address
        self.resolver_address = settings.resolver_address
        
        registry_abi_path = os.path.join(os.path.dirname(__file__), "registry_abi.json")
        resolver_abi_path = os.path.join(os.path.dirname(__file__), "resolver_abi.json")
        try:
            with open(registry_abi_path, "r", encoding="utf-8") as f:
                registry_abi = json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo ABI crucial no encontrado en la ruta: {registry_abi_path}")
            raise

        try:
            with open(resolver_abi_path, "r", encoding="utf-8") as f:
                resolver_abi = json.load(f)
        except FileNotFoundError:
            logger.error(f"Archivo ABI crucial no encontrado en la ruta: {resolver_abi_path}")
            raise
        
        self.registry_contract = self.w3.eth.contract(address=self.registry_address, abi=registry_abi)
        self.resolver_contract = self.w3.eth.contract(address=self.resolver_address, abi=resolver_abi)
    
    # Helper para calcular el Namehash
    def get_namehash(self, domain: str) -> bytes:
        if not domain:
            return b'\x00' * 32
        parts = domain.split(".")
        node = b'\x00' * 32
        for part in reversed(parts):
            label_hash = self.w3.keccak(text=part)
            node = self.w3.solidity_keccak(["bytes32", "bytes32"], [node, label_hash])
        return node
    
    # Resolución Directa: Traduce nombre -> wallet
    def resolve(self, domain: str) -> str:
        """Obtiene la dirección de la wallet (addr) asignada a un dominio ENS."""
        try:
            node_hash = self.get_namehash(domain)
            # Verificar si tiene un Resolver asignado en el Registry
            resolver_assigned = self.registry_contract.functions.resolver(node_hash).call()
            if resolver_assigned == "0x0000000000000000000000000000000000000000":
                logger.warning(f"El dominio {domain} no tiene un resolver asignado.")
                return "0x0000000000000000000000000000000000000000"

            # Consultar la dirección directamente al Resolver contract
            address = self.resolver_contract.functions.addr(node_hash).call()
            return address
        except Exception as e:
            logger.error(f"Error al resolver el dominio {domain}: {str(e)}")
            return "0x0000000000000000000000000000000000000000"

    # Comparador Directo: Compara si el dominio apunta a una wallet dada
    def resolve_and_compare(self, domain: str, expected_address: str) -> bool:
        """Compara si la dirección resuelta coincide con la esperada."""
        resolved_address = self.resolve(domain)
        if resolved_address == "0x0000000000000000000000000000000000000000":
            return False
        return resolved_address.lower() == expected_address.lower()

    # Resolución Reversa: Traduce wallet -> nombre (.reverse)
    def reverse_resolve(self, address: str) -> str:
        """Obtiene el nombre de dominio ENS asociado a una wallet usando resolución reversa."""
        try:
            # Formateo de dirección según exige el estándar EIP-181 (sin '0x' y en minúsculas)
            clean_address = address.lower().replace("0x", "")
            address_label_hash = self.w3.keccak(text=clean_address)
            
            # Construccion del nodo reverso de forma secuencial: reverse -> addr.reverse -> [address].addr.reverse
            addr_reverse_node = self.get_namehash("addr.reverse")
            final_reverse_node = self.w3.solidity_keccak(["bytes32", "bytes32"], [addr_reverse_node, address_label_hash])

            # consultar al Resolver por el nombre asociado a ese nodo
            name = self.resolver_contract.functions.name(final_reverse_node).call()
            return name
        except Exception as e:
            logger.error(f"Error al resolver reverso para la wallet {address}: {str(e)}")
            return ""

    # Comparador Reverso: Compara si la wallet apunta al dominio esperado
    def reverse_resolve_and_compare(self, address: str, expected_domain: str) -> bool:
        """Compara si el nombre resuelto de la wallet coincide con el esperado."""
        resolved_name = self.reverse_resolve(address)
        if not resolved_name:
            return False
        return resolved_name.strip().lower() == expected_domain.strip().lower()

    # Resolución Bidireccional Cruzada
    def resolve_bidirectional(self, domain: str, address: str) -> bool:
        """
        Realiza una validación bidireccional estricta.
        Devuelve True únicamente si:
        1. El dominio resuelve a la dirección provista (Direccional).
        2. La dirección provista resuelve de vuelta al mismo dominio (Reversa).
        """
        direct_match = self.resolve_and_compare(domain, address)
        reverse_match = self.reverse_resolve_and_compare(address, domain)
        
        is_valid = direct_match and reverse_match
        
        if not is_valid:
            logger.warning(
                f"Fallo en la resolución cruzada. "
                f"Directo ({domain} -> {address}): {direct_match}. "
                f"Reverso ({address} -> {domain}): {reverse_match}."
            )
            
        return is_valid

                        
@lru_cache()
def get_ENS_manager() -> ENSManager:
    """
    Inyecta un singleton de ENSManager para ser usado en toda la aplicación.
    """
    return ENSManager()
    
    