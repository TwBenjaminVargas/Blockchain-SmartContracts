// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Registry.sol";
import "./Resolver.sol";
contract Registrar {

    Registry public ens;
    address public defaultResolver;
    bytes32 public rootNode;

    constructor(address ensAddr, address resolverAddr, bytes32 node) {
        ens = Registry(ensAddr);
        defaultResolver = resolverAddr;
        rootNode = node;
    }

    function register(bytes32 label, address _owner) public {
        // Calcular el nodo completo final
        bytes32 node = keccak256(abi.encodePacked(rootNode, label));
        
        // Control de propiedad (FIFS)
        address currentOwner = ens.owner(node);
        require(currentOwner == address(0) || currentOwner == msg.sender, "Nombre ya registrado por otro usuario");

        // Asignar temporalmente el subnodo al contrato para poder configurarlo
        ens.setSubnodeOwner(rootNode, label, address(this));

        // Setear el Resolver por defecto en el Registry
        ens.setResolver(node, defaultResolver);

        // Configurar la dirección del usuario en el Resolver
        Resolver(defaultResolver).setAddr(node, _owner);

        // Entregarle finalmente la propiedad total del nodo al usuario
        ens.setOwner(node, _owner);
    }
}