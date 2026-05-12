//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract CFP {
    // Evento que se emite cuando alguien registra una propuesta
    event ProposalRegistered(
        bytes32 proposal,
        address sender,
        uint256 blockNumber
    );

    // Estructura que representa una propuesta
    struct ProposalData {
        address sender;
        uint256 blockNumber;
        uint256 timestamp;
    }


    mapping(bytes32 => ProposalData) public proposalData;

    bytes32[] public proposals;

    uint256 public closingTime;

    bytes32 public callId;

    address public creator;


    modifier checkClosingTime(uint256 _closingTime)
    {
        require( block.timestamp <= _closingTime, "El cierre de la convocatoria no puede estar en el pasado");
        _;
    }

    modifier closingTimeHasNotPassed()
    {
        require(block.timestamp <= closingTime, "Convocatoria cerrada");
        _;
    }

    modifier proposalIsUnique(bytes32 proposal)
    {
        require(proposalData[proposal].sender == address(0), "La propuesta ya ha sido registrada");
        _;
    }

    modifier onlyCreator()
    {
        require(msg.sender == creator, "Solo el creador puede hacer esta llamada");
        _;
    }

    /** Construye un llamado con un identificador y un tiempo de cierre.
     *  Si el `timestamp` del bloque actual es mayor o igual al tiempo de cierre especificado,
     *  revierte con el mensaje "El cierre de la convocatoria no puede estar en el pasado".
     */
    constructor(bytes32 _callId, uint256 _closingTime)
    checkClosingTime(_closingTime)
    {
        callId = _callId;
        closingTime = _closingTime;
        creator = msg.sender;
    }

    /** Permite registrar una propuesta espec.
     *  Registra al emisor del mensaje como emisor de la propuesta.
     *  Si el timestamp del bloque actual es mayor que el del cierre del llamado,
     *  revierte con el error "Convocatoria cerrada"
     *  Si ya se ha registrado una propuesta igual, revierte con el mensaje
     *  "La propuesta ya ha sido registrada"
     *  Emite el evento `ProposalRegistered`
     */
    function registerProposal(bytes32 proposal) public
    closingTimeHasNotPassed()
    proposalIsUnique(proposal)
    {
        proposalData[proposal] = ProposalData(msg.sender, block.number, block.timestamp);
        proposals.push(proposal);
        emit ProposalRegistered(proposal, msg.sender, block.number);
    }

    /** Permite registrar una propuesta especificando un emisor.
     *  Sólo puede ser ejecutada por el creador del llamado. Si no es así, revierte
     *  con el mensaje "Solo el creador puede hacer esta llamada"
     *  Si el timestamp del bloque actual es mayor que el del cierre del llamado,
     *  revierte con el error "Convocatoria cerrada"
     *  Si ya se ha registrado una propuesta igual, revierte con el mensaje
     *  "La propuesta ya ha sido registrada"
     *  Emite el evento `ProposalRegistered`
     */
    function registerProposalFor(bytes32 proposal, address sender) public 
    onlyCreator()
    closingTimeHasNotPassed()
    proposalIsUnique(proposal)
    {
        proposalData[proposal] = ProposalData(sender, block.number, block.timestamp);
        proposals.push(proposal);
        emit ProposalRegistered(proposal, sender, block.number);

    }

    /** Devuelve la cantidad de propuestas registradas.
     */
    function proposalCount() public view returns (uint256)
    {
        return proposals.length;
    }

    /** Devuelve el timestamp en el que se ha registrado una propuesta.
     *  Si la propuesta no está registrada, devuelve cero.
     */
    function proposalTimestamp( bytes32 proposal) public view returns (uint256) 
    {
        return proposalData[proposal].timestamp;
    }
}
