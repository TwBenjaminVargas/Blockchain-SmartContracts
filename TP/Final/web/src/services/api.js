import axios from 'axios'
import { URL } from '../config/constants'
// Creamos una instancia centralizada de Axios
const api = axios.create({
  // URL base de API

  baseURL: URL.url_base, 
  timeout: 5000, // Si la API tarda más de 5 segundos, cancela la petición
  headers: {
    'Content-Type': 'application/json'
  }
})


export const getAdminAddress = async () => {

  try {
    const response = await api.get(URL.admin_address)
    return response.data.address 
  } catch (error) {
    console.error('Error al obtener la dirección del admin desde la API:', error)
    throw error
  }
}

export const getCreators = async () => {
  try {
    const response = await api.get(URL.creators)
    return response.data
  } catch (error) {
    console.error('Error al obtener el listado de creadores:', error)
    throw error
  }
}

export const getRegistrationStatus = async (address) => {
  try {
    const response = await api.get(URL.registrationStatus.replace(':address', address))
    return response.data
  } catch (error) {
    console.error(`Error al obtener el estado de registro para ${address}:`, error)
    throw error
  }
}

export const registerUser = async (payload) => {
  try {
    const response = await api.post(URL.registerUser, payload)
    return response.data
  } catch (error) {
    console.error('Error al registrar el usuario:', error)
    throw error
  }
}

export const getContractAddress = async () => {
  try {
    const response = await api.get(URL.contract_address)
    return response.data.address
  } catch (error) {
    console.error('Error al obtener la dirección del contrato factoría:', error)
    throw error
  }
}

export const getAdminNonce = async () => {
  try {
    const response = await api.get(URL.admin_nonce)
    return response.data.nonce
  } catch (error) {
    console.error('Error al obtener la dirección del contrato factoría:', error)
    throw error
  }
}


export const authorizeUser = async (address, payload) => {
  const response = await api.post(URL.authorizeUser.replace(':address', address), payload)
  return response.data
}

export const unauthorizeUser = async (address, payload) => {
  const response = await api.post(URL.unauthorizeUser.replace(':address', address), payload)
  return response.data
}

export const getUsers = async () => {
  const response = await api.get(URL.users)
  return response.data
}

export const getAuthorizationRequests = async () => {
  const response = await api.get(URL.authorization_requests)
  return response.data
}

export const updateRegistration = async (address, payload) => {
  const response = await api.patch(URL.updateRegistration.replace(':address',address), payload)
  return response.data
}

export const getUserCalls = async (address) => {
  try {
    const response = await api.get(URL.getUserCalls.replace(':address', address))
    return response.data
  } catch (error) {
    console.error(`Error al obtener los llamados para la dirección ${address}:`, error)
    throw error
  }
}

export const createCall = async (payload) => {
  try {
    const response = await api.post(URL.createCall, payload)
    return response.data
  } catch (error) {
    console.error('Error al registrar la convocatoria en la base de datos:', error)
    throw error
  }
}
export const getGlobalCalls = async () => {
  try {
    const response = await api.get(URL.global_calls)
    return response.data
  } catch (error) {
    console.error('Error al obtener el catálogo de llamados globales:', error)
    throw error
  }
}
export const getProposalsByCall = async (callId) => {
  try {
    const response = await api.get(URL.getProposalsByCall.replace(':call_id', callId))
    return response.data
  } catch (error) {
    console.error(`Error al obtener propuestas del llamado ${callId}:`, error)
    throw error
  }
}


export const getProposalReceipt = async (proposalId) => {
  try {
    const response = await api.get(URL.getProposalReceipt.replace(':proposalId', proposalId))
    return response.data
  } catch (error) {
    console.error(`Error al obtener el recibo para la propuesta ${proposalId}:`, error)
    throw error
  }
}


export const submitPostClosing = async (payload) => {
  try {
    // Si envías archivos binarios físicos reales, recordar configurar 'Content-Type': 'multipart/form-data'
    const response = await api.post(URL.submitPostClosing, payload, {
      headers: {
        'Content-Type': payload instanceof FormData ? 'multipart/form-data' : 'application/json'
      }
    })
    return response.data
  } catch (error) {
    console.error('Error en la entrega post-cierre de la propuesta:', error)
    throw error
  }
}

export const verifyProposalReceipt = async (payload) => {
  try {
    const response = await api.post(URL.verifyProposal, payload)
    return response.data
  } catch (error) {
    console.error('Error al verificar el recibo de la propuesta:', error)
    throw error
  }
}

export const downloadProposalFiles = async (proposalId) => {
  try {
    const response = await api.get(URL.downloadProposalFiles.replace(':proposal_id', proposalId), {
      responseType: 'blob' // Indica a Axios que maneje la respuesta como archivo binario (Blob)
    })
    
    // Crear un link temporal en el DOM para forzar la descarga del ZIP de forma nativa en el navegador
    const blob = new Blob([response.data], { type: 'application/x-zip-compressed' })
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `propuesta_${proposalId.substring(0, 10)}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    return true
  } catch (error) {
    console.error(`Error al descargar el archivo ZIP de la propuesta ${proposalId}:`, error)
    throw error
  }
}

export const getCallById = async (callId) => {
  try {
    const response = await api.get(URL.getCallById.replace(':call_id', callId))
    return response.data
  } catch (error) {
    console.error(`Error al obtener el llamado ${callId}:`, error)
    throw error
  }
}

export const getClosingTime = async (callId) => {
  try {
    const response = await api.get(URL.getClosingTime.replace(':call_id', callId))
    return response.data
  } catch (error) {
    console.error(`Error al obtener el tiempo de cierre para el llamado ${callId}:`, error)
    throw error
  }
}

export const registerProposal = async (payload) => {
  try {
    const response = await api.post(URL.registerProposal, payload)
    return response.data
  } catch (error) {
    console.error('Error al registrar la propuesta en el servidor:', error)
    throw error
  }
}

export const getProposalReceiptPostClosing = async (proposalId) => {
  try {
    const response = await api.get(URL.getProposalReceiptPostClosing.replace(':proposal_id', proposalId))
    return response.data
  } catch (error) {
    console.error(`Error al obtener el recibo post-cierre para la propuesta ${proposalId}:`, error)
    throw error
  }
}

export const getENSAddresses = async (proposalId) => {
  try {
    const response = await api.get(URL.getENSAddresses)
    return response.data
  } catch (error) {
    console.error(`Error al obtener las direcciones ENS`, error)
    throw error
  }
}