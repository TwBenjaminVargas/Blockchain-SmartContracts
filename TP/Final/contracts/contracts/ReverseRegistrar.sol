// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Registry.sol";

interface IResolver {
    function setName(bytes32 node, string calldata _name) external;
}

contract ReverseRegistrar {
    // namehash('addr.reverse')
    bytes32 public constant ADDR_REVERSE_NODE = 0x91d1777781884d03a6757a803996e38de2a42967fb37eeaca72729271025a9e2;

    Registry public immutable registry;
    IResolver public defaultResolver;

    constructor(address _registry, address _defaultResolver) {
        registry = Registry(_registry);
        defaultResolver = IResolver(_defaultResolver);
    }

    /**
     * Reclama el nodo reverso y asigna un dueño.
     */
    function claim(address owner) public returns (bytes32) {
        return claimWithResolver(owner, address(0));
    }

    /**
     * Reclama el nodo reverso, asigna resolutor y transfiere el nodo al dueño final.
     */
    function claimWithResolver(address owner, address resolver) public returns (bytes32) {
        bytes32 label = sha3HexAddress(msg.sender);
        bytes32 node = keccak256(abi.encodePacked(ADDR_REVERSE_NODE, label));
        address currentOwner = registry.owner(node);

        // Configura el resolver si es necesario
        if (resolver != address(0) && resolver != registry.resolver(node)) {
            if (currentOwner != address(this)) {
                registry.setSubnodeOwner(ADDR_REVERSE_NODE, label, address(this));
                currentOwner = address(this);
            }
            registry.setResolver(node, resolver);
        }

        // Configura el dueño final si es diferente
        if (currentOwner != owner) {
            registry.setSubnodeOwner(ADDR_REVERSE_NODE, label, owner);
        }

        return node;
    }

    /**
     * Atajo en una sola transacción: Reclama, configura el resolver por defecto y guarda el nombre.
     */
    function setName(string calldata name) public returns (bytes32) {
        bytes32 node = claimWithResolver(address(this), address(defaultResolver));
        defaultResolver.setName(node, name);
        return node;
    }

    /**
     * Versión optimizada en Assembly (Yul) para convertir dirección a hash de texto en minúsculas.
     * Basado exactamente en el apéndice de la especificación oficial del EIP-181.
     */
    function sha3HexAddress(address addr) private pure returns (bytes32 ret) {
    assembly {
        // Tabla de búsqueda de caracteres ASCII (0-9, a-f)
        let lookup := 0x3031323334353637383961626364656600000000000000000000000000000000
        let memPtr := mload(0x40)

        // Bucle 'for' estructurado en Yul que reemplaza los saltos jmp/loop
        for { let i := 40 } i { } {
            // Caracter derecho
            i := sub(i, 1) // restar 1 a i
            mstore8(add(memPtr, i), byte(and(addr, 0xf), lookup)) // mascara para obtener los ultimos 4 bits y buscar el caracter correspondiente, luego almacenar en memoria en posicion i
            addr := div(addr, 0x10)
            
            // Caracter izquierdo
            i := sub(i, 1)
            mstore8(add(memPtr, i), byte(and(addr, 0xf), lookup))
            addr := div(addr, 0x10)
        }

        // Calcula el keccak256 de los 40 bytes en memoria
        ret := keccak256(memPtr, 40)
    }
}
}