// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Registry.sol";
import "./Resolver.sol";
import "./ReverseRegistrar.sol";

/**
 * LlamadosRegistrar
 * Permite a los usuarios registrar primero un nombre y luego configurar sus registros (dirección y reverso) en un llamado posterior.
 */
contract LlamadosRegistrar {

    Registry public immutable ens;
    Resolver public immutable defaultResolver;
    bytes32 public immutable rootNode;
    ReverseRegistrar public immutable reverseRegistrar;
    string public rootSuffix;

    /**
     * Inicializa las dependencias y el sufijo del dominio raíz.
     */
    constructor(address ensAddr, address resolverAddr, bytes32 node, address reverseRegistrarAddr, string memory _rootSuffix) {
        ens = Registry(ensAddr);
        defaultResolver = Resolver(resolverAddr);
        rootNode = node;
        reverseRegistrar = ReverseRegistrar(reverseRegistrarAddr);
        rootSuffix = string(abi.encodePacked(".", _rootSuffix));
    }

    /**
     * Registra y reserva la propiedad del subdominio para el msg.sender.
     * No configura direcciones ni reverso aún; solo establece quién es el dueño del nodo.
     * label: El nombre en texto plano (ej: "benja").
     */
    function register(string calldata label) external {
        bytes32 labelHash = keccak256(abi.encodePacked(label));
        bytes32 node = keccak256(abi.encodePacked(rootNode, labelHash));
        
        // Control de propiedad (FIFS)
        address currentOwner = ens.owner(node);
        require(currentOwner == address(0) || currentOwner == msg.sender, "Nombre ya registrado por otro usuario");

        // Asignar el subnodo directamente al usuario que lo reclama en el Registry
        ens.setSubnodeOwner(rootNode, labelHash, msg.sender);
    }

    /**
     * Configura el Resolver y hace que el subdominio apunte al Contrato Destino.
     * label: El nombre en texto plano (ej: "llamadas").
     * targetContract: La dirección del contrato al que apuntará el subdominio.
     */
    function setupRecords(string calldata label, address targetContract) external {
        bytes32 labelHash = keccak256(abi.encodePacked(label));
        bytes32 node = keccak256(abi.encodePacked(rootNode, labelHash));

        // Solo el dueño del subdominio puede configurarlo
        require(ens.owner(node) == msg.sender, "No eres el dueno de este subdominio");

        //Tomar control temporal para configurar el Registry
        ens.setSubnodeOwner(rootNode, labelHash, address(this));

        // Setear el Resolver por defecto
        ens.setResolver(node, address(defaultResolver));

        // Hacer que el subdominio apunte a la dirección del contrato
        defaultResolver.setAddr(node, targetContract);

        // Devolverle la propiedad del subdominio al usuario original
        ens.setOwner(node, msg.sender);
    }
}