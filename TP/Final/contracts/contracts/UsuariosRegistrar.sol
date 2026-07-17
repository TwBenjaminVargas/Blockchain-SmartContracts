// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Registry.sol";
import "./Resolver.sol";
import "./ReverseRegistrar.sol";

/**
 * Permite a los usuarios registrar un subdominio propio y configurar su resolución inversa en una sola transacción.
 */
contract UsuariosRegistrar {

    Registry public immutable ens;
    Resolver public immutable defaultResolver;
    bytes32 public immutable rootNode;
    ReverseRegistrar public immutable reverseRegistrar;
    string public rootSuffix;

    /**
     * Inicializa las dependencias del sistema ENS y el gestor de registro inverso.
     * ensAddr Dirección del Registry central de ENS.
     * resolverAddr Dirección del Resolver por defecto para almacenar los registros de los usuarios.
     * node El namehash del nodo raíz que este contrato administra (ej: namehash('usuarios.cfp')).
     * reverseRegistrarAddr Dirección del contrato ReverseRegistrar autorizado.
     * _rootDomain El dominio raíz para el cual se registrarán los subdominios.
     */
    constructor(address ensAddr, address resolverAddr, bytes32 node, address reverseRegistrarAddr, string memory _rootSuffix) {
        ens = Registry(ensAddr);
        defaultResolver = Resolver(resolverAddr);
        rootNode = node;
        reverseRegistrar = ReverseRegistrar(reverseRegistrarAddr);
        rootSuffix = string(abi.encodePacked(".", _rootSuffix)); // Añade un punto al inicio del sufijo del dominio raíz para formar nombres completos.
    }

    /**
     * Registra un subdominio directo y configura la resolución inversa de la wallet de manera atómica.
     * Convierte el string en un hash de etiqueta, verifica disponibilidad, configura ENS y llama al ReverseRegistrar.
     * label: El nombre de texto plano que el usuario quiere para su subdominio (ej: "benja").
     */
    function register(string calldata label) external {
        // Calcular hashes iniciales
        bytes32 labelHash = keccak256(abi.encodePacked(label));
        bytes32 node = keccak256(abi.encodePacked(rootNode, labelHash));
        
        // Control de propiedad (FIFS - First Come, First Served)
        address currentOwner = ens.owner(node);
        require(currentOwner == address(0) || currentOwner == msg.sender, "Nombre ya registrado por otro usuario");

        // Asignar temporalmente el subnodo al contrato para poder configurarlo en el Registry
        ens.setSubnodeOwner(rootNode, labelHash, address(this));

        // Setear el Resolver por defecto en el Registry
        ens.setResolver(node, address(defaultResolver));

        // Configurar la dirección del usuario (msg.sender) en el Resolver
        defaultResolver.setAddr(node, msg.sender);

        // Entregarle finalmente la propiedad total del subdominio directo al usuario
        ens.setOwner(node, msg.sender);

        // Construir el dominio de texto completo (ej: "benja.usuarios.cfp")
        string memory fullDomain = string(abi.encodePacked(label, rootSuffix));

        // 8. Ordenar al ReverseRegistrar que configure la resolución inversa para el msg.sender original
        reverseRegistrar.setNameForAddr(msg.sender, fullDomain);
    }
}