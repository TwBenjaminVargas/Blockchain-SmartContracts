import { ethers } from 'ethers'
import { getContractAddress } from './api'
import { FILES } from '../config/constants'

async function getContractInstance() {
  if (!window.ethereum) {
    throw new Error('MetaMask no está disponible en este navegador.')
  }

  const provider = new ethers.BrowserProvider(window.ethereum)
  const signer = await provider.getSigner()

  const addressData = await getContractAddress()
  const factoryAddress = typeof addressData === 'string' ? addressData : addressData.address

  if (!factoryAddress) {
    throw new Error('No se pudo obtener la dirección del contrato desde el servidor.')
  }

  return new ethers.Contract(ethers.getAddress(factoryAddress.trim()), FILES.CFP_FACTORY_ABI, signer)
}

export async function registerInFactory() {
  const contract = await getContractInstance()
  const tx = await contract.register()
  return await tx.wait()
}

export async function createInFactory(callId, timestamp) {
  const contract = await getContractInstance()
  
  // Aseguramos que el callId mantenga el formato correcto para bytes32 de ethers
  const formattedCallId = callId.startsWith('0x') ? callId : `0x${callId}`
  const bigIntTimestamp = BigInt(timestamp)

  // Ejecutamos la función en el Smart Contract
  const tx = await contract.create(formattedCallId, bigIntTimestamp)
  
  // Esperamos a que la transacción se mine en la red
  return await tx.wait()
}