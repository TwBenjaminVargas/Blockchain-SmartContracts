// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
import "./Registry.sol";

contract Registrar {
    Registry public ens;
    bytes32 public rootNode;

    constructor(address ensAddr, bytes32 node) {
        ens = Registry(ensAddr);
        rootNode = node;
    }

    function register(bytes32 label, address _owner) public {

        bytes32 node = keccak256(abi.encodePacked(rootNode, label));
        
        address currentOwner = ens.owner(node);
        // FIFS
        require(currentOwner == address(0) || currentOwner == msg.sender, "Nombre ya registrado por otro usuario");

        ens.setSubnodeOwner(rootNode, label, _owner);
    }
}