//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CFP {
    // Evento que se emite cuando alguien registra una propuesta
    event ProposalRegistered(
        bytes32 proposal,
        address sender,
        uint256 blockNumber
    );

    // Evento emitido cuando se suben los archivos post-cierre
    event FilesReceived(bytes32 indexed proposal, address sender, uint256 timestamp);

    // Evento emitido cuando se habilita a un usuario a retirar su garantía
    event guaranteeWithdrawAuthorized(address indexed user);

    // Evento emitido cuando se cierra la recepción de archivos
    event FilesSubmissionClosed();

    event guaranteesLiquidated(address indexed creator, uint256 amount);

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

    // address de un administrador
    address public admin;

    // address de fabrica
    address public creator;

    bool public isFileSubmissionOpen;

    mapping(bytes32 => bool) public filesDelivered;
    
    // Garantía que debe depositar los creadores de propuestas
    uint256 public guarantee;
    
    IERC20 public token;
    
    address[] public usersAuthorizedToWithdrawGuarantee;

    mapping (address => bool) public isAuthorizedToWithdrawGuarantee;


    modifier checkClosingTime(uint256 _closingTime)
    {
        require( block.timestamp < _closingTime, "El cierre de la convocatoria no puede estar en el pasado");
        _;
    }

    modifier closingTimeHasNotPassed()
    {
        require(block.timestamp <= closingTime, "Convocatoria cerrada");
        _;
    }

    modifier closingTimeHasPassed() {
        require(block.timestamp > closingTime, "La convocatoria todavia esta abierta");
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

    modifier guaranteeIsZero()
    {
        require(guarantee == 0, "La garantia del llamado debe ser cero para utilizar este metodo");
        _;
    }

    modifier onlyAdmin()
    {
        require(msg.sender == admin, "Solo el administrador puede hacer esta llamada");
        _;
    }
    
    modifier fileSubmissionIsOpen() {
        require(isFileSubmissionOpen, "La entrega de archivos no esta abierta");
        _;
        
    }
    modifier fileSubmissionIsClosed() {
        require(!isFileSubmissionOpen, "La entrega de archivos debe estar cerrada");
        _;
        
    }

    /** Construye un llamado con un identificador y un tiempo de cierre.
     *  Si el `timestamp` del bloque actual es mayor o igual al tiempo de cierre especificado,
     *  revierte con el mensaje "El cierre de la convocatoria no puede estar en el pasado".
     */
    constructor(bytes32 _callId, uint256 _closingTime, address _admin, uint256 _guarantee, IERC20 _token)
    checkClosingTime(_closingTime)
    {
        callId = _callId;
        closingTime = _closingTime;
        creator = msg.sender;
        admin = _admin;
        guarantee = _guarantee;
        token = _token;
        isFileSubmissionOpen = true;
    }

    /** 
     * Cobra la garantía del pagador, si la garantía es mayor a cero.
     * Requiere que el pagador tenga saldo suficiente y que haya aprobado la transferencia.
     * Si no se cumplen estas condiciones, revierte con un mensaje de error.
    */
    function _takeGuarantee(address payer) internal {
    if (guarantee > 0) {
        bool success = token.transferFrom(payer, address(this), guarantee);
        require(success, "Fallo el cobro de la garantia");
    }
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
        _takeGuarantee(msg.sender);
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
    guaranteeIsZero()
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

    /** Permite registrar en cadena la entrega final posterior al cierre del llamado.
     *  Verifica que el tiempo de cierre haya pasado y que la propuesta exista.
     */
    function recordFilesReception(bytes32 proposal) public 
    closingTimeHasPassed()
    fileSubmissionIsOpen()
    {
        // Verificar que la propuesta realmente exista en el contrato
        require(proposalData[proposal].sender != address(0), "La propuesta no existe");
        // Evitar doble registro
        require(!filesDelivered[proposal], "Los archivos ya fueron registrados previamente");
        // Asentar el estado on-chain
        filesDelivered[proposal] = true;
        emit FilesReceived(proposal, msg.sender, block.timestamp);
    }

    /**
     * Habilita a un usuario puntual a retirar su garantía mediante Patrón Pull
     */
    function authorizeGuaranteeWithdraw(address usuario) public
    onlyAdmin()
    closingTimeHasPassed()
    fileSubmissionIsClosed()
    
    {
        require(!isAuthorizedToWithdrawGuarantee[usuario], "El usuario ya fue autorizado");
        require(guarantee > 0, "No hay costo de garantia");

        usersAuthorizedToWithdrawGuarantee.push(usuario);
        isAuthorizedToWithdrawGuarantee[usuario] = true;

        emit guaranteeWithdrawAuthorized(usuario);
    }

    /**
     * Cierra la recepción de archivos, impidiendo que se puedan registrar más entregas.
     */
    function closeFileSubmission() public
    onlyAdmin()
    fileSubmissionIsOpen()
    closingTimeHasPassed()
    {
        isFileSubmissionOpen = false;
        emit FilesSubmissionClosed();
    }


    /**
     * Liquidación de garantías no reclamadas a la cuenta del Creador.
     * Solo puede ejecutarse cuando la convocatoria cerró y ya no se aceptan archivos.
     */
    function claimDefaultingGuarantees() public onlyAdmin() closingTimeHasPassed() fileSubmissionIsClosed()
    {

        uint256 balance = token.balanceOf(address(this));
        
        // Calcular cuánto pertenece a reembolsos ya autorizados pero que los usuarios aún no retiraron
        uint256 compromised = 0;
        compromised += usersAuthorizedToWithdrawGuarantee.length * guarantee;

        require(balance > compromised, "No hay garantias sobrantes para liquidar");
        uint256 settleAmount = balance - compromised;

        bool success = token.transfer(admin, settleAmount);
        require(success, "Fallo la liquidacion al creador");

        emit guaranteesLiquidated(admin, settleAmount);
    }
}
