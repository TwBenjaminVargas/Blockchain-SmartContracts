//SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.19;

/// @title Votación
contract Ballot {
    // Esta estructura representa a un votante
    struct Voter {
        bool canVote; // si es verdadero, la persona puede votar
        bool voted; // si es verdadero, la persona ya votó
        uint vote; // índice de la propuesta elegida.
    }

    // Este tipo representa a una propuesta
    struct Proposal {
        bytes32 name; // nombre (hasta 32 bytes)
        uint voteCount; // votos recibidos por la propuesta
    }

    bool private _started;
    bool private _ended;

    address public chairperson;

    // Variable de estado con los votantes
    mapping(address => Voter) public voters;
    // Cantidad de votantes
    uint public numVoters;

    // Arreglo dinámico de propuestas.
    Proposal[] public proposals;

    /// Crea una nueva votación para elegir entre `proposalNames`.
    constructor(bytes32[] memory proposalNames) {
        chairperson = msg.sender;
        require(
            proposalNames.length > 1,
            "There should be at least two proposals."
        );
        for (uint i = 0; i < proposalNames.length; i++) {
            // `Proposal({...})` crea un objeto temporal
            // de tipo Proposal y  `proposals.push(...)`
            // lo agrega al final de `proposals`.
            proposals.push(Proposal({name: proposalNames[i], voteCount: 0}));
        }
    }

    // Le da a `voter` el derecho a votar.
    // Solamente puede ser ejecutado por `chairperson`.
    // No se puede hacer si
    //  * El votante ya puede votar
    //  * La votación ya comenzó
    // Actualiza numVoters
    function giveRightToVote(address voter) public {
        require(
            msg.sender == chairperson,
            "Only chairperson can invoke this function."
        );
        require(!voters[voter].voted, "The voter already voted.");
        require(!voters[voter].canVote, "Voter already has right to vote");
        require(!_started, "Voting has already started.");
        voters[voter].canVote = true;
        numVoters += 1;
    }

    // Quita a `voter` el derecho a votar.
    // Solamente puede ser ejecutado por `chairperson`.
    // No se puede hacer si
    //  * El votante no puede votar
    //  * La votación ya comenzó
    // Actualiza numVoters
    function withdrawRightToVote(address voter) public {
        require(
            msg.sender == chairperson,
            "Only chairperson can invoke this function."
        );
        require(voters[voter].canVote, "Voter has no right to vote");
        require(!voters[voter].voted, "The voter already voted.");
        require(!_started, "Voting has already started.");
        voters[voter].canVote = false;
        numVoters -= 1;
    }

    // Le da a todas las direcciones contenidas en `list` el derecho a votar.
    // Solamente puede ser ejecutado por `chairperson`.
    // No se puede ejecutar si la votación ya comenzó
    // Si el votante ya puede votar, no hace nada.
    // Actualiza numVoters
    function giveAllRightToVote(address[] memory list) public {
        require(
            msg.sender == chairperson,
            "Only chairperson can invoke this function."
        );
        require(!_started, "Voting has already started.");
        for (uint i = 0; i < list.length; i++) {
            if (!voters[list[i]].canVote) {
                voters[list[i]].canVote = true;
                numVoters += 1;
            }
        }
    }

    // Devuelve la cantidad de propuestas
    function numProposals() public view returns (uint) {
        return proposals.length;
    }

    // Habilita el comienzo de la votación
    // Solo puede ser invocada por `chairperson`
    // No puede ser invocada una vez que la votación ha comenzado
    function start() public {
        require(
            msg.sender == chairperson,
            "Only chairperson can invoke this function."
        );
        require(!_started, "Voting has already started.");
        _started = true;
    }

    // Indica si la votación ha comenzado
    function started() public view returns (bool) {
        return _started;
    }

    // Finaliza la votación
    // Solo puede ser invocada por `chairperson`
    // Solo puede ser invocada una vez que la votación ha comenzado
    // No puede ser invocada una vez que la votación ha finalizado
    function end() public {
        require(
            msg.sender == chairperson,
            "Only chairperson can invoke this function."
        );
        require(_started, "Voting has not started yet.");
        require(!_ended, "Voting has already ended.");
        _ended = true;
    }

    // Indica si la votación ha finalizado
    function ended() public view returns (bool) {
        return _ended;
    }

    // Vota por la propuesta `proposals[proposal].name`.
    // Requiere que la votación haya comenzado y no haya terminado
    // Si `proposal` está fuera de rango, lanza
    // una excepción y revierte los cambios.
    // El votante tiene que estar habilitado
    // No se puede votar dos veces
    // No se puede votar si la votación aún no comenzó
    // No se puede votar si la votación ya terminó
    function vote(uint proposal) public {
        Voter storage sender = voters[msg.sender];
        require(sender.canVote, "Has no right to vote");
        require(!sender.voted, "Already voted.");
        require(_started, "Voting has not started yet.");
        require(!_ended, "Voting has already ended.");
        require(proposal < proposals.length, "Invalid proposal.");
        sender.voted = true;
        sender.vote = proposal;
        proposals[proposal].voteCount += 1;
    }

    /// Calcula la propuestas ganadoras
    /// Devuelve un array con los índices de las propuestas ganadoras.
    // Solo se puede ejecutar si la votación terminó.
    // Si no hay votos, devuelve un array de longitud 0
    // Si hay un empate en el primer puesto, la longitud
    // del array es la cantidad de propuestas que empatan
    function winningProposals()
        public
        view
        returns (uint[] memory winningProposal_)
    {
        require(_ended, "Voting has not ended yet.");
        uint[] memory wproposal = new uint[](proposals.length);
        uint maxVotes = 0;
        uint tie=0;
        for (uint i=0; i<proposals.length; i++)
        {
            if(maxVotes < proposals[i].voteCount)
            {
                maxVotes = proposals[i].voteCount;
                wproposal[0] = i;
                tie=0;
            }            
            else if(maxVotes == proposals[i].voteCount && maxVotes != 0)
            {
                tie++;
                wproposal[tie] = i;
            }
        }

        if(maxVotes > 0)
        {
            winningProposal_ = new uint[](tie+1);
            for (uint i = 0; i <= tie; i++) {
                winningProposal_[i] = wproposal[i];
            }
        }
    }

    // Devuelve un array con los nombres de las
    // propuestas ganadoras.
    // Solo se puede ejecutar si la votación terminó.
    // Si no hay votos, devuelve un array de longitud 0
    // Si hay un empate en el primer puesto, la longitud
    // del array es la cantidad de propuestas que empatan
    function winners() public view returns (bytes32[] memory winners_) {

        require(_ended, "Voting has not ended yet.");
        Proposal[] memory wproposals = new Proposal[](proposals.length);
        
        uint maxVotes = 0;
        uint tie=0;
        for (uint i=0; i<proposals.length; i++)
        {
            if(maxVotes < proposals[i].voteCount)
            {
                maxVotes = proposals[i].voteCount;
                wproposals[0] = proposals[i];
                tie=0;
            }            
            else if(maxVotes == proposals[i].voteCount && maxVotes != 0)
            {
                tie++;
                wproposals[tie] = proposals[i];
            }
        }

        if(maxVotes > 0)
        {
            winners_ = new bytes32[](tie+1);
            for (uint i = 0; i <= tie; i++) {
                winners_[i] = wproposals[i].name;
            }
        }
    }
}
