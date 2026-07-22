import { ethers } from 'ethers'
import { getTokenAddress } from './api' // Importa tu llamada al endpoint GET /settings/token-address
import { FILES } from '../config/constants' // Debe contener el ABI del ERC20 / BENCOIN

export class TokenService {
  /**
   * Obtiene la instancia conectada del contrato BENCOIN.
   */
  async _getContractInstance() {
    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()

    // Obtiene la dirección del token desde la API Backend
    const response = await getTokenAddress()
    const tokenAddress = typeof response === 'string' ? response : response.address

    if (!tokenAddress) {
      throw new Error('No se pudo obtener la dirección del token BENCOIN desde el servidor.')
    }

    return new ethers.Contract(ethers.getAddress(tokenAddress.trim()), FILES.BENCOIN_ABI, signer)
  }

  /**
   * Consulta la tolerancia / aprobación (allowance) otorgada por un propietario a un gastador.
   */
  async allowance(owner, spender) {
    const contract = await this._getContractInstance()
    const formattedOwner = ethers.getAddress(owner)
    const formattedSpender = ethers.getAddress(spender)

    // Llama al método estándar de ERC20
    return await contract.allowance(formattedOwner, formattedSpender)
  }

  /**
   * Consulta el balance de BENCOIN de una dirección dada.
   */
  async balanceOf(account) {
    const contract = await this._getContractInstance()
    const formattedAccount = ethers.getAddress(account)

    return await contract.balanceOf(formattedAccount)
  }

  /**
   * Consulta la tasa de cambio (rate) configurada en BENCOIN (1 ETH = X Tokens).
   */
  async rate() {
    const contract = await this._getContractInstance()
    return await contract.rate()
  }

  /**
   * Aprueba a un tercero (spender) a disponer de cierta cantidad de tokens del usuario actual.
   */
  async approve(spender, amount) {
  const contract = await this._getContractInstance()
  const formattedSpender = ethers.getAddress(spender)
  
  // Convertir directamente a BigInt
  const bigIntAmount = typeof amount === 'bigint' ? amount : BigInt(amount.toString())

  const tx = await contract.approve(formattedSpender, bigIntAmount)
  return await tx.wait()
}

/**
   * Permite al usuario adquirir BENCOINs ingresando la cantidad legible de tokens.
   * desiredTokens Cantidad de BEN a comprar (ej: 150 o "150.5")
   */
  async buy(desiredTokens) {
    const contract = await this._getContractInstance()
    
    //Obtener la tasa de cambio del contrato (ej: 1000n = 1000 tokens por ETH)
    const currentRate = await contract.rate() // BigInt
    
    // Escalar los tokens deseados a sus 18 decimales (Wei)
    const tokensInBaseUnits = ethers.parseEther(desiredTokens.toString())
    
    //Calcular el costo en ETH (en Wei): Tokens en Wei / Rate
    const ethCostInWei = tokensInBaseUnits / BigInt(currentRate)

    //Enviar la transacción pasando el valor equivalente en ETH
    const tx = await contract.buy({ value: ethCostInWei })
    return await tx.wait()
  }

  /**
   * Permite al usuario vender sus BENCOINs ingresando la cantidad legible de tokens.
   * Cantidad de BEN a vender (ej: 150 o "150.5")
   */
  async sell(tokenAmount) {
    const contract = await this._getContractInstance()

    // Escalar la cantidad de tokens deseada a sus 18 decimales (unidades base)
    // El contrato recibe el valor exacto con sus 18 decimales incorporados
    const tokensInBaseUnits = ethers.parseEther(tokenAmount.toString())

    const tx = await contract.sell(tokensInBaseUnits)
    return await tx.wait()
  }

  /**
   * Permite transferir tokens desde una cuenta origen (from) hacia una cuenta destino (to)
   * aprovechando una autorización previa.
   */
  async transferFrom(from, to, amount) {
    const contract = await this._getContractInstance()
    const formattedFrom = ethers.getAddress(from)
    const formattedTo = ethers.getAddress(to)
    const bigIntAmount = typeof amount === 'bigint' ? amount : BigInt(amount.toString())

    const tx = await contract.transferFrom(formattedFrom, formattedTo, bigIntAmount)
    return await tx.wait()
}
}




// Exportamos una única instancia (Singleton)
export const tokenService = new TokenService()