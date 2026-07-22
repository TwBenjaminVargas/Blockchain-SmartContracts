import { ethers } from 'ethers'
import { getCallContractAddress } from './api'
import { FILES } from '../config/constants'

export class CFPService {
  /**
   * Obtiene la instancia del contrato CFP para un callId específico.
   */
  async _getContractInstance(callId) {
    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()

    // Consume el endpoint GET /calls/{call_id}/contract de la API Backend
    const response = await getCallContractAddress(callId)
    const cfpAddress = typeof response === 'string' ? response : response.address

    if (!cfpAddress) {
      throw new Error(`No se pudo obtener la dirección del contrato CFP para el callId: ${callId}`)
    }

    return new ethers.Contract(ethers.getAddress(cfpAddress.trim()), FILES.CFP_ABI, signer)
  }


  /**
   * Registra una propuesta en el contrato CFP.
   * Signature Solidity: registerProposal(bytes32 proposal)
   */
  async registerProposal(callId, proposalHash) {
    const contract = await this._getContractInstance(callId)
    const formattedProposal = proposalHash.startsWith('0x') ? proposalHash : `0x${proposalHash}`

    const tx = await contract.registerProposal(formattedProposal)
    return await tx.wait()
  }

  /**
   * Autoriza a un usuario para retirar su garantía.
   */
  async authorizeGuaranteeWithdraw(callId, userAddress) {
    const contract = await this._getContractInstance(callId)
    const formattedUser = ethers.getAddress(userAddress)

    const tx = await contract.authorizeGuaranteeWithdraw(formattedUser)
    return await tx.wait()
  }

  /**
   * Cierra la recepción de archivos en la convocatoria.
   */
  async closeFileSubmission(callId) {
    const contract = await this._getContractInstance(callId)

    const tx = await contract.closeFileSubmission()
    return await tx.wait()
  }

  /**
   * Liquida las garantías no reclamadas a favor del creador/admin.
   */
  async claimDefaultingGuarantees(callId) {
    const contract = await this._getContractInstance(callId)

    const tx = await contract.claimDefaultingGuarantees()
    return await tx.wait()
  }

  /**
   * Consulta el estado del flag público `isFileSubmissionOpen`.
   */
  async isFileSubmissionOpen(callId) {
    const contract = await this._getContractInstance(callId)
    return await contract.isFileSubmissionOpen()
  }

  /**
   * Consulta si una dirección está autorizada para retirar la garantía.
   */
  async isAuthorizedToWithdrawGuarantee(callId, userAddress) {
    const contract = await this._getContractInstance(callId)
    const formattedUser = ethers.getAddress(userAddress)

    return await contract.isAuthorizedToWithdrawGuarantee(formattedUser)
  }
  /**
     * Verifica si una propuesta (hash) ya existe en la blockchain.
     * Retorna true si la propuesta ya fue guardada on-chain.
     */
    async getProposalData(callId, proposalHash) {
    const contract = await this._getContractInstance(callId)
    const formattedProposal = proposalHash.startsWith('0x') ? proposalHash : `0x${proposalHash}`

    // Llama al getter generado automáticamente por Solidity para public mapping proposalData
    const proposalData = await contract.proposalData(formattedProposal)
    
    // Si sender es ZeroAddress (0x0000...), no existe el registro en la blockchain
    const exists = proposalData && proposalData.sender !== ethers.ZeroAddress
    
    return {
      exists,
      sender: proposalData.sender,
      blockNumber: proposalData.blockNumber ? proposalData.blockNumber.toString() : '0',
      timestamp: proposalData.timestamp ? proposalData.timestamp.toString() : '0'
    }
  }

  /**
   * Consulta el estado del flag público isFileSubmissionOpen en el Smart Contract.
   * Devuelve true si la recepción de archivos continúa abierta, false si se ha cerrado.
   */
  async isFileSubmissionOpen(callId) {
    const contract = await this._getContractInstance(callId)
    return await contract.isFileSubmissionOpen()
  }
  
  async closeFileSubmission(callId) {
    const contract = await this._getContractInstance(callId, true)
    const tx = await contract.closeFileSubmission()
    return await tx.wait()
  }
}


// Exportamos una instancia única (Singleton) para simplificar su importación
export const cfpService = new CFPService()