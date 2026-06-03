import axios from 'axios'

// Creamos una instancia centralizada de Axios
const api = axios.create({
  // URL base de API
  //TODO que la url venga de variables de entorno
  baseURL: 'http://localhost:3000/api', 
  timeout: 5000, // Si la API tarda más de 5 segundos, cancela la petición
  headers: {
    'Content-Type': 'application/json'
  }
})


export const getAdminAddress = async () => {

  try {
    const response = await api.get('/config/admin-address')
    return response.data.address 
  } catch (error) {
    console.error('Error al obtener la dirección del admin desde la API:', error)
    throw error
  }
}