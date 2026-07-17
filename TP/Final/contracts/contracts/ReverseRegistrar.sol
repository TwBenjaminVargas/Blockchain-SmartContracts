// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Registry.sol";
import "./Resolver.sol";
/**
 * Gestiona y configura el registro inverso de ENS para las direcciones Ethereum.
 * Permite enlazar una wallet (dirección) a un nombre de dominio legible (texto).
 */
contract ReverseRegistrar {
    // namehash de 'addr.reverse'
    bytes32 public constant ADDR_REVERSE_NODE = 0x91d1777781884d03a6757a803996e38de2a42967fb37eeaca72729271025a9e2;

    Registry public immutable registry;
    Resolver public defaultResolver;

    /**
     * Constructor que inicializa el registro central y el resolutor por defecto.
     */
    constructor(address _registry, address _defaultResolver) {
        registry = Registry(_registry);
        defaultResolver = Resolver(_defaultResolver);
    }

    /**
     * Crea el nodo reverso para quien llama a la función y le asigna un dueño.
     * @param owner Dirección de la cuenta que controlará el nodo creado.
     */
    function claim(address owner) public returns (bytes32) {
        return claimWithResolver(owner, address(0));
    }

    /**
     * Crea el nodo reverso, le asigna un resolutor específico y define su dueño final.
     * @param owner Dirección del propietario final del nodo.
     * @param resolver Dirección del contrato encargado de resolver los datos de este nodo.
     */
    function claimWithResolver(address owner, address resolver) public returns (bytes32) {
        return _claimWithResolver(msg.sender, owner, resolver);
    }

    /**
     * Permite a otro contrato autorizado configurar de forma atómica 
     * la resolución inversa de una wallet de usuario en una sola transacción.
     * @param _addr Dirección de la wallet del usuario que se va a mapear.
     * @param name El nombre de dominio completo en texto (ej: "usuario.usuarios.cfp").
     */
    function setNameForAddr(address _addr, string calldata name) public returns (bytes32) {
        // Reclama el nodo reverso apuntando a este contrato temporalmente con el resolver por defecto
        bytes32 node = _claimWithResolver(_addr, address(this), address(defaultResolver));
        // Guarda el string del nombre en el Resolver
        defaultResolver.setName(node, name);
        // Devuelve la propiedad del nodo reverso al usuario original por seguridad
        registry.setSubnodeOwner(ADDR_REVERSE_NODE, sha3HexAddress(_addr), _addr);
        return node;
    }

    /**
     * Centraliza los cálculos de nodos, validaciones de ENS y transferencias.
     * Está adaptado para procesar cualquier dirección origen que se le envíe.
     */
    function _claimWithResolver(address _origin, address owner, address resolver) internal returns (bytes32) {
        bytes32 label = sha3HexAddress(_origin);
        bytes32 node = keccak256(abi.encodePacked(ADDR_REVERSE_NODE, label));
        address currentOwner = registry.owner(node);

        if (resolver != address(0) && resolver != registry.resolver(node)) {
            if (currentOwner != address(this)) {
                registry.setSubnodeOwner(ADDR_REVERSE_NODE, label, address(this));
                currentOwner = address(this);
            }
            registry.setResolver(node, resolver);
        }

        if (currentOwner != owner) {
            registry.setSubnodeOwner(ADDR_REVERSE_NODE, label, owner);
        }

        return node;
    }

    /**
     * Crea el nodo, le asigna el resolutor base y guarda el nombre en texto para msg.sender.
     * @param name Nombre de dominio en formato texto legible que se quiere asociar a la wallet.
     */
    function setName(string calldata name) public returns (bytes32) {
        bytes32 node = claimWithResolver(address(this), address(defaultResolver));
        defaultResolver.setName(node, name);
        return node;
    }

    /**
     * Transforma la dirección binaria en un hash hexadecimal en minúsculas.
     * Emplea bloques optimizados en Assembly (Yul) siguiendo de forma exacta el estándar del EIP-181.
     */
    function sha3HexAddress(address addr) private pure returns (bytes32 ret) {
        assembly {
            let lookup := 0x3031323334353637383961626364656600000000000000000000000000000000
            let memPtr := mload(0x40)

            for { let i := 40 } i { } {
                i := sub(i, 1)
                mstore8(add(memPtr, i), byte(and(addr, 0xf), lookup))
                addr := div(addr, 0x10)
                
                i := sub(i, 1)
                mstore8(add(memPtr, i), byte(and(addr, 0xf), lookup))
                addr := div(addr, 0x10)
            }

            ret := keccak256(memPtr, 40)
        }
    }
}