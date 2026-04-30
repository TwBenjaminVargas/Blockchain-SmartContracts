// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Task.sol";

/// @title Tablero de tareas
/// @notice Crea tareas, registra sus estados y mantiene listados por etapa.
contract TaskBoard is ITaskRegistry {

    struct TaskInfo {
        state status;
        uint256 index;
    }

    mapping(address => TaskInfo) public tasks;

    event TaskCreated(address taskAddress, address reporter, string description);
    event TaskMovedToInProgress(address taskAddress, uint256 index);
    event TaskMovedToDone(address taskAddress, uint256 index);
    
    
    address[] public todo;

    address[] public inProgress;

    address[] public done;


    
    modifier onlyRegisteredTask() {
        require(tasks[msg.sender].status != state.None, "La tarea no esta registrada en el tablero");
        _;
    }

    modifier ToDoStateRequired 
    {
        require(tasks[msg.sender].status != state.InProgress, "La tarea ya esta en progreso");
        require(tasks[msg.sender].status != state.Completed, "La tarea ya fue completada");
        _;
    }

    modifier InProgressStateRequired {
        require(tasks[msg.sender].status != state.Completed, "La tarea ya fue completada");
        require(tasks[msg.sender].status != state.ToDo, "La tarea no esta en progreso");
        _;        
    }

    
    // Registra que una tarea pasó a estado InProgress.
    // Requisitos:
    //  * El emisor debe ser una tarea registrada.
    //  * La tarea no debe estar en progreso ni finalizada.
    // Efectos:
    //  * Quita la tarea de `todo`.
    //  * Actualiza su estado e índice.
    //  * La agrega al arreglo `inProgress`.
    //  * Emite `TaskMovedToInProgress`.
    function taskStarted() public
    onlyRegisteredTask
    ToDoStateRequired
    {
        TaskInfo storage info = tasks[msg.sender];
        uint256 indexToRemove = info.index;
        uint256 lastIdx = todo.length - 1;
        address lastTask = todo[lastIdx];

        todo[indexToRemove] = lastTask;
        tasks[lastTask].index = indexToRemove;
        todo.pop();

        info.status = state.InProgress;
        info.index = inProgress.length;
        inProgress.push(msg.sender);

        Task(msg.sender).started();
            
        emit TaskMovedToInProgress(msg.sender, info.index);

    }

    // Registra que una tarea pasó a estado Done.
    // Requisitos:
    //  * El emisor debe ser una tarea registrada.
    //  * La tarea no debe estar finalizada.
    //  * La tarea debe estar en progreso.
    // Efectos:
    //  * Quita la tarea de `inProgress`.
    //  * Actualiza su estado e índice.
    //  * La agrega al arreglo `done`.
    //  * Emite `TaskMovedToDone`.
    function taskCompleted() public
    onlyRegisteredTask
    InProgressStateRequired
    {
        TaskInfo storage info = tasks[msg.sender];

        uint256 indexToRemove = info.index;
        uint256 lastIdx = inProgress.length - 1;
        address lastTask = inProgress[lastIdx];

        inProgress[indexToRemove] = lastTask;
        tasks[lastTask].index = indexToRemove; 
        inProgress.pop();

        info.status = state.Completed;
        info.index = done.length;
        done.push(msg.sender);

        Task(msg.sender).completed();
        emit TaskMovedToDone(msg.sender, info.index);
    }

    function createTask(string memory description) public returns (address taskAddress)
    {
        Task newTask = new Task(description, msg.sender);
        taskAddress = address(newTask);
        todo.push(taskAddress);
        tasks[taskAddress] = TaskInfo(state.ToDo, todo.length - 1);
        emit TaskCreated(taskAddress, msg.sender, description);
    }

    function todoCount() public view returns (uint256)
    {
        return todo.length;
    }

    function inProgressCount() public view returns (uint256) 
    {
        return inProgress.length;
    }

    function doneCount() public view returns (uint256)
    {
        return done.length;
    }

    function todoByAssignee(address worker) public view returns (address[] memory)
    {
        uint256 count = 0;
    
        for (uint256 i = 0; i < todo.length; i++) {
            if (Task(todo[i]).assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < todo.length; i++) {
            if (Task(todo[i]).assignee() == worker) {
                result[index] = todo[i];
                index++;
            }
        }

        return result;
    }

    function inProgressByAssignee(address worker) public view returns (address[] memory)
    {
        uint256 count = 0;
    
        for (uint256 i = 0; i < inProgress.length; i++) {
            if (Task(inProgress[i]).assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < inProgress.length; i++) {
            if (Task(inProgress[i]).assignee() == worker) {
                result[index] = inProgress[i];
                index++;
            }
        }

        return result;
    }

    function doneByAssignee(address worker) public view returns (address[] memory)
    {
        uint256 count = 0;
    
        for (uint256 i = 0; i < done.length; i++) {
            if (Task(done[i]).assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < done.length; i++) {
            if (Task(done[i]).assignee() == worker) {
                result[index] = done[i];
                index++;
            }
        }

        return result;
    }
}