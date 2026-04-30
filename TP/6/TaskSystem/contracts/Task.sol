// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

enum state { None, ToDo, InProgress, Completed }
// Interfaz que debe implementar el tablero para recibir
// notificaciones de cambios de estado de una tarea.
interface ITaskRegistry {
    // Notifica al tablero que la tarea pasó a estado en progreso.
    function taskStarted() external;

    // Notifica al tablero que la tarea pasó a estado finalizada.
    function taskCompleted() external;
}

/// @title Tarea individual del sistema
contract Task {

    ITaskRegistry private factory;
    string public description;
    address public reporter;
    address public assignee;

    uint256 public assignedAt;
    uint256 public startedAt;
    uint256 public completedAt;

    state private currentState;
    
    event TaskAssigned(address reporter, address assignee, uint256 timestamp);
    event TaskStarted(address assignee, uint256 timestamp);
    event TaskCompleted(address assignee, uint256 timestamp);
    
    constructor(string memory _description, address _reporter)
    {
        factory = ITaskRegistry(msg.sender);
        description = _description;
        reporter = _reporter;
        currentState = state.ToDo;
    }

    modifier reporterRequired() {
        require(msg.sender == reporter, "Solo el reporter puede realizar esta accion");
        _;
    }

    modifier assigneeRequired() {
        require(msg.sender == assignee, "Solo el assignee puede realizar esta accion");
        _;
    }


    modifier pendingStateRequired() {
        require(currentState == state.ToDo, "La tarea ya ha comenzado");
        _;
    }

    modifier inProgressStateRequired() {
        require(currentState == state.InProgress, "La tarea no esta en progreso");
        _;
    }


    function assign(address worker) public
    reporterRequired
    pendingStateRequired
    {
        assignee = worker;
        assignedAt = block.timestamp;
        emit TaskAssigned(reporter, worker, assignedAt);
    }

    function start() public
    assigneeRequired
    pendingStateRequired
    {
        currentState = state.InProgress;
        factory.taskStarted();
        startedAt = block.timestamp;
        emit TaskStarted(assignee, startedAt);
    }

    function complete() public
    assigneeRequired
    inProgressStateRequired
    {
        currentState = state.Completed;
        factory.taskCompleted();
        completedAt = block.timestamp;
        emit TaskCompleted(assignee, completedAt);
    }

    function started() public view returns (bool)
    {
        return currentState == state.InProgress || currentState == state.Completed;
    }

    function completed() public view returns (bool)
    {
        return currentState == state.Completed;
    }



}