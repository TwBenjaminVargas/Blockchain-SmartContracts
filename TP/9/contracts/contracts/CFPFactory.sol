//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./CFP.sol";

contract CFPFactory {
    // Evento que se emite cuando se crea un llamado a presentación de propuestas
    event CFPCreated(address creator, bytes32 callId, CFP cfp);

    //Evento que se emite cuando una cuenta llama a register para solicitar autorización
    event CreatorRegistered(address indexed creator);

    //Dueño de la factoria autoriza a una cuenta mediante authorize()
    event CreatorAuthorized(address indexed creator);

    // Dueño de la factoria quita la autorización a una cuenta mediante unauthorize()
    event CreatorUnauthorized(address indexed creator);

    // Estructura que representa un llamado
    struct CallForProposals {
        address creator;
        CFP cfp;
    }
    enum AddressStatus { None, Pending, Authorized, Unauthorized }

    modifier onlyOwner()
    {
        require(msg.sender == owner, "Solo el creador puede hacer esta llamada");
        _;
    }

    modifier callDoesNotExist(bytes32 callId)
    {
        require(calls[callId].creator == address(0), "El llamado ya existe");
        _;
    }

     modifier callExists(bytes32 callId)
    {
        require(calls[callId].creator != address(0), "El llamado no existe");
        _;
    }

     modifier onlyAuthorized()
    {
        require(addressStatus[msg.sender] == AddressStatus.Authorized, "No autorizado");
        _;
    }
    modifier addressIsAuthorized(address account)
    {
        require(addressStatus[account] == AddressStatus.Authorized, "No autorizado");
        _;
    }

    modifier notRegistered()
    {
        require(addressStatus[msg.sender] == AddressStatus.None, "Ya se ha registrado");
        _;
    }


    address public owner;
    
    mapping(bytes32 => CallForProposals) public calls;
    
    mapping (address => CFP[]) private createdByMap;

    address[] public creators;

    address[] private pendingList;

    mapping (address => AddressStatus) private addressStatus;
    


    constructor() {owner = msg.sender;}

    // Devuelve la cantidad de cuentas que han creado llamados.
    function creatorsCount() public view returns (uint256) {return creators.length;}

    // Devuelve la cantidad de llamados creados por `creator`
    function createdByCount(address creator) public view returns (uint256) { return createdByMap[creator].length;}

    /// Devuelve el identificador del llamado que está en la posición `index` de la lista de llamados creados por `creator`
    function createdBy( address creator,uint256 index) public view returns (bytes32) 
    {
        return createdByMap[creator][index].callId();
    }

    // Devuelve la cantidad de registraciones pendientes.
    // Sólo puede ser ejecutada por el dueño de la factoría
    // En caso contrario revierte con el mensaje "Solo el creador puede hacer esta llamada".
    function pendingCount() public view onlyOwner() returns (uint256) {return pendingList.length;}

    // Devuelve la registración pendiente con índice `index`
    // Sólo puede ser ejecutada por el dueño de la factoría
    // En caso contrario revierte con el mensaje "Solo el creador puede hacer esta llamada".
    function getPending(uint256 index) public view onlyOwner() returns (address)
    {return pendingList[index];}

    // Devuelve la lista de todas las registraciones pendientes.
    // Sólo puede ser ejecutada por el dueño de la factoría
    // En caso contrario revierte con el mensaje "Solo el creador puede hacer esta llamada".
    function getAllPending() public view onlyOwner() returns (address[] memory)
    {return pendingList;}
    
    // Devuelve verdadero si una cuenta se ha registrado, tanto si su estado es pendiente como si ya se la ha autorizado.
    function isRegistered(address account) public view returns (bool)
    {return addressStatus[account] != AddressStatus.None && addressStatus[account] != AddressStatus.Unauthorized;}

    // Devuelve verdadero si una cuenta está autorizada a crear llamados.
    function isAuthorized(address account) public view returns (bool) {return addressStatus[account] == AddressStatus.Authorized;}

    /** Crea un llamado, con un identificador y un tiempo de cierre
     *  Si ya existe un llamado con ese identificador, revierte con el mensaje de error "El llamado ya existe"
     *  Si el emisor no está autorizado a crear llamados, revierte con el mensaje "No autorizado"
     */
    function create(bytes32 callId, uint256 timestamp) public
    callDoesNotExist(callId)
    onlyAuthorized()
    returns (CFP)
    {
        CFP cfp = new CFP(callId, timestamp);
        calls[callId] = CallForProposals(msg.sender, cfp);
        if (createdByMap[msg.sender].length == 0) {
            creators.push(msg.sender);
        }
        createdByMap[msg.sender].push(cfp);
        emit CFPCreated(msg.sender, callId, cfp);
    }

    /**
     * Crea un llamado, estableciendo a `creator` como creador del mismo.
     * Sólo puede ser invocada por el dueño de la factoría.
     * Se comporta en todos los demás aspectos como `createFor(bytes32 callId, uint timestamp)`
     */
    function createFor(bytes32 callId,uint timestamp,address creator) public 
    onlyOwner()
    callDoesNotExist(callId)
    addressIsAuthorized(creator)
    returns (CFP)
    {
        CFP cfp = new CFP(callId, timestamp);
        calls[callId] = CallForProposals(creator, cfp);
        if (createdByMap[creator].length == 0) {
            creators.push(creator);
        }
        createdByMap[creator].push(cfp);
        emit CFPCreated(creator, callId, cfp);
    }

    /** Permite que una cuenta se registre para poder crear llamados.
     *  El registro queda en estado pendiente hasta que el dueño de la factoría lo autorice.
     *  Si ya se ha registrado, revierte con el mensaje "Ya se ha registrado"
     */
    function register() public
    notRegistered()
    {
        addressStatus[msg.sender] = AddressStatus.Pending;
        pendingList.push(msg.sender);
        emit CreatorRegistered(msg.sender);
    }


    /** Permite a un usuario registrar una propuesta, para un llamado con identificador `callId`.
     *  Si el llamado no existe, revierte con el mensaje  "El llamado no existe".
     *  Registra la propuesta en el llamado asociado con `callId` y pasa como creador la dirección del emisor del mensaje.
     */
    function registerProposal(bytes32 callId, bytes32 proposal) public
    callExists(callId)
    {
        calls[callId].cfp.registerProposalFor(proposal, msg.sender);
    }


    /** Autoriza a una cuenta a crear llamados.
     *  Sólo puede ser ejecutada por el dueño de la factoría.
     *  En caso contrario revierte con el mensaje "Solo el creador puede hacer esta llamada".
     *  Si la cuenta se ha registrado y está pendiente, la quita de la lista de pendientes.
     */

    /* Comentario de alumno:
    * En el enunciado no se indica que hacer si la cuenta no se ha registrado,
    * por lo que se asume que el dueño de la factoría puede autorizar a cualquier cuenta,
    * incluso si no se ha registrado previamente. En este caso, simplemente se establece el 
    * estado de la cuenta como autorizada sin necesidad de eliminarla de la lista de pendientes, 
    * ya que no estaría en ella. 
    * Si la cuenta se ha registrado y está pendiente, entonces sí se elimina de la lista de pendientes al autorizarla.
    */

    function authorize(address creator) public 
    onlyOwner()
    {
        addressStatus[creator] = AddressStatus.Authorized;
        for (uint256 i = 0; i < pendingList.length; i++) {
            if (pendingList[i] == creator) {
                // Eliminar la cuenta de la lista de pendientes
                pendingList[i] = pendingList[pendingList.length - 1];
                pendingList.pop();
                emit CreatorAuthorized(creator);
                break;
            }
        }
    }

    /** Quita la autorización de una cuenta para crear llamados.
     *  Sólo puede ser ejecutada por el dueño de la factoría.
     *  En caso contrario revierte con el mensaje "Solo el creador puede hacer esta llamada".
     *  Si la cuenta se ha registrado y está pendiente, la quita de la lista de pendientes.
     */
    function unauthorize(address creator) public 
    onlyOwner()
    {
        addressStatus[creator] = AddressStatus.Unauthorized;
        for (uint256 i = 0; i < pendingList.length; i++) {
            if (pendingList[i] == creator) {
                // Eliminar la cuenta de la lista de pendientes
                pendingList[i] = pendingList[pendingList.length - 1];
                pendingList.pop();
                emit CreatorUnauthorized(creator);
                break;
            }
        }

    }





}
