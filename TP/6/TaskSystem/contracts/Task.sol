// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

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

    uint256 public assignetAt;
    uint256 public startedAt;
    uint256 public completedAt;

    enum state { Pending, InProgress, Completed }
    state private currentState;
    
    event TaskAssigned(address reporter, address assignee, uint256 timestamp);
    event TaskStarted(address assignee, uint256 timestamp);
    event TaskCompleted(address assignee, uint256 timestamp)
    
    constructor(string _description, address _reporter)
    {
        factory = ITaskRegistry(msg.sender);
        description = _description;
        reporter = _reporter;
    }

    modifier reporterRequired() {
        require(msg.sender == reporter, "Solo el reporter puede realizar esta acción");
    }

    modifier assigneeRequired() {
        require(msg.sender == assignee, "Solo el assignee puede realizar esta acción");
    }


    modifier pendingStateRequired() {
        require(currentState == state.Pending, "La tarea ya ha comenzado");
        _;
    }

    modifier inProgressStateRequired() {
        require(currentState == state.InProgress, "La tarea no está en progreso");
        _;
    }


    function assign(address worker) public
    reporterRequired
    pendingStateRequired
    {
        assignee = worker;
        assignetAt = block.timestamp;
        emit TaskAssigned(reporter, worker, assignetAt);
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
        return currentState == state.InProgress;
    }

    function completed() public view returns (bool)
    {
        return currentState == state.Completed;
    }



}