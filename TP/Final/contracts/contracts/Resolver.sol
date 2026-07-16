// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
import "./Registry.sol";

contract Resolver {

    event AddrChanged(bytes32 indexed node, address a);
    event NameChanged(bytes32 indexed node, string name);

    Registry public ens;
    
    // Almacenamiento para EIP-137 (Resolución directa: node -> address)
    mapping(bytes32 => address) private _addresses;
    
    // Almacenamiento para EIP-181 (Resolución reversa: reverseNode -> name)
    mapping(bytes32 => string) private _names;


    modifier only_owner(bytes32 node) {
        require(ens.owner(node) == msg.sender, "No autorizado");
        _;
    }


    constructor(address ensAddr) {
        ens = Registry(ensAddr);
    }

    // EIP-137: Resolución Directa

    // Retorna la dirección asociada a un nodo (la palabra constant cambió por view)
    function addr(bytes32 node) public view returns (address) {
        return _addresses[node];
    }

    // Guarda la dirección para un nodo (solo lo puede hacer el dueño)
    function setAddr(bytes32 node, address _addr) public only_owner(node) {
        _addresses[node] = _addr;
        emit AddrChanged(node, _addr); // Requiere "emit"
    }


    // EIP-181: Resolución Reversa

    // Retorna el nombre asociado al nodo reverso de una dirección
    function name(bytes32 node) public view returns (string memory) {
        return _names[node];
    }

    // Guarda el nombre de reversa para un nodo reverso
    function setName(bytes32 node, string memory _name) public only_owner(node) {
        _names[node] = _name;
        emit NameChanged(node, _name);
    }


    // EIP-165: Detección de Interfaces
    function supportsInterface(bytes4 interfaceID) public pure returns (bool) {
        return 
            interfaceID == 0x01ffc9a7 || // ERC-165 (supportsInterface)
            interfaceID == 0x3b3b57de || // ERC-137 (Resolución directa: addr)
            interfaceID == 0x691f3431;   // ERC-181 (Resolución reversa: name)
    }

    fallback() external {
        revert("Operacion no soportada");
    }
}