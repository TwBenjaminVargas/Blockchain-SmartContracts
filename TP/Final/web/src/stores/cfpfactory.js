import { defineStore } from 'pinia'
import { ref } from 'vue'
import { registerInFactory } from '../services/cfpfactory'

export const useContractStore = defineStore('contract', () => {
  const isLoading = ref(false)
  const errorMessage = ref('')
  const successMessage = ref('')

  async function registerCreator() {
    isLoading.value = true
    errorMessage.value = ''
    successMessage.value = ''
    
    try {
      const receipt = await registerInFactory()
      successMessage.value = 'Solicitud de registro enviada con éxito. Estado: Pendiente de autorización.'
      return receipt
    } catch (error) {
      if (error.code === 'ACTION_REJECTED') {
        errorMessage.value = 'Firma rechazada en MetaMask.'
      } else if (error.message && error.message.includes('Ya se ha registrado')) {
        errorMessage.value = 'Esta cuenta ya se encuentra registrada o con una solicitud pendiente.'
      } else {
        errorMessage.value = error.message || 'Ocurrió un error inesperado al interactuar con la blockchain.'
      }
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    errorMessage,
    successMessage,
    registerCreator
  }
})