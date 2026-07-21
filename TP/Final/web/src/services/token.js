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
    const bigIntAmount = ethers.parseEther(amount.toString())

    const tx = await contract.approve(formattedSpender, bigIntAmount)
    return await tx.wait()
  }

  /**
   * Permite al usuario adquirir BENCOINs enviando ETH.
   */
  async buy(ethAmount) {
    const contract = await this._getContractInstance()
    const weiValue = ethers.parseEther(ethAmount.toString())

    // Se envía ETH mediante la opción `value` de la transacción payable
    const tx = await contract.buy({ value: weiValue })
    return await tx.wait()
  }

  /**
   * Permite al usuario vender sus BENCOINs a cambio de ETH.
   */
  async sell(tokenAmount) {
    const contract = await this._getContractInstance()
    const bigIntTokenAmount = ethers.parseEther(tokenAmount.toString())

    const tx = await contract.sell(bigIntTokenAmount)
    return await tx.wait()
  }
}

// Exportamos una única instancia (Singleton)
export const tokenService = new TokenService()