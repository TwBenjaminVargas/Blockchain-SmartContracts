// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Task.sol";

/// @title Tablero de tareas
/// @notice Crea tareas, registra sus estados y mantiene listados por etapa.
contract TaskBoard is ITaskRegistry {

    event TaskCreated(address taskAddress, address reporter, string description)
    event TaskMovedToInProgress(address taskAddress, uint256 index)
    event TaskMovedToDone(address taskAddress, uint256 index)
    
    
    address[] public todo;
    mapping (address => Task) private ToDoMap;

    address[] public inProgress;
    mapping (address => Task) private InProgressMap;

    address[] public done;
    mapping (address => Task) private DoneMap;

    
    modifier taskRegisteredRequired() {
        require(ToDoMap[msg.sender] != Task(address(0)) || InProgressMap[msg.sender] != Task(address(0)) || DoneMap[msg.sender] != Task(address(0)), "La tarea no está registrada en el tablero");
        _;
    }

    modifier ToDoStateRequired {
        require(ToDoMap[msg.sender] != Task(address(0)), "La tarea no está en estado ToDo");
        _;
    }

    modifier InProgressStateRequired {
        require(InProgressMap[msg.sender] != Task(address(0)), "La tarea no está en estado InProgress");
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
    taskRegisteredRequired
    ToDoStateRequired
    {
            Task task = ToDoMap[msg.sender];
            delete ToDoMap[msg.sender];
            for (uint256 i = 0; i < todo.length; i++) {
                if (todo[i] == msg.sender) {
                    todo[i] = todo[todo.length - 1];
                    todo.pop();
                    break;
                }
            }
    
            InProgressMap[msg.sender] = task;
            inProgress.push(msg.sender);
            task.started();
            emit TaskMovedToInProgress(msg.sender, inProgress.length - 1);

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
    taskRegisteredRequired
    InProgressStateRequired
    {
            Task task = InProgressMap[msg.sender];
            delete InProgressMap[msg.sender];
            for (uint256 i = 0; i < inProgress.length; i++) {
                if (inProgress[i] == msg.sender) {
                    inProgress[i] = inProgress[inProgress.length - 1];
                    inProgress.pop();
                    break;
                }
            }
    
            DoneMap[msg.sender] = task;
            done.push(msg.sender);
            task.completed();
            emit TaskMovedToDone(msg.sender, done.length - 1);
    }

    function createTask(string memory description) public returns (address taskAddress)
    {
        Task newTask = new Task(description, msg.sender);
        taskAddress = address(newTask);
        ToDoArr.push(taskAddress);
        ToDoMap[taskAddress] = newTask;
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
            if (ToDoMap[todo[i]].assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < todo.length; i++) {
            if (ToDoMap[todo[i]].assignee() == worker) {
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
            if (InProgressMap[inProgress[i]].assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < inProgress.length; i++) {
            if (InProgressMap[inProgress[i]].assignee() == worker) {
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
            if (DoneMap[done[i]].assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < done.length; i++) {
            if (DoneMap[done[i]].assignee() == worker) {
                result[index] = done[i];
                index++;
            }
        }

        return result;
    }
}