// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract BENCOIN is ERC20{
    
    // Tasa de cambio: 1 ETH = 1000 Tokens
    uint256 public rate;

    // Definimos el nombre, símbolo
    constructor(uint256 _rate) 
        ERC20("BENCOIN", "BEN")
    {
        rate = _rate;
    }

    // Permite al usuario adquirir BENCOINs
    function buy() public payable {
        require(msg.value > 0, "Debes enviar ETH");

        // Cálculo: (ETH enviado * tasa)
        // Como msg.value está en Wei y el token usa 18 decimales, la proporción se mantiene
        uint256 tokenAmount = msg.value * rate;

        // Se transfieren los tokens al comprador (o se minan)
        _mint(msg.sender, tokenAmount);
    }

    // Permite al usuario vender sus BENCOINs a cambio de ETH
    function sell(uint256 tokenAmount) public {
    require(tokenAmount > 0, "Debes vender al menos 1 token");
    require(balanceOf(msg.sender) >= tokenAmount, "No tienes suficientes tokens");

    // Calcular cuanto ETH le corresponde al usuario
    uint256 ethToReturn = tokenAmount / rate;

    // Verificar que el contrato tenga ETH suficiente para pagar
    require(address(this).balance >= ethToReturn, "El contrato no tiene suficiente reserva de ETH");

    // Quemar o retirar los tokens del usuario
    _burn(msg.sender, tokenAmount);

    // Transferir el ETH de vuelta al usuario
    payable(msg.sender).transfer(ethToReturn);
}

}