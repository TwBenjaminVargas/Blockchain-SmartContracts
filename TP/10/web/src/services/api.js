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