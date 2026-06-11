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