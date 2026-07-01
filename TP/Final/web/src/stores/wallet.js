import { defineStore } from 'pinia'
import { ethers } from 'ethers'
import { getAdminAddress, getRegistrationStatus } from '../services/api'

export const useWalletStore = defineStore('wallet', {
  state: () => ({
    account: null,
    userRole: null, // 'admin', 'creator', 'pending', 'guest'
    isLoading: false,
    error: null,
    registration: {
      status: 'pending',
      name: '',
      description: '',
      nonce: 0
    }
  }),

  actions: {
    async connectMetaMask() {
      if (!window.ethereum) {
        this.error = 'MetaMask no está instalado.'
        return false
      }

      this.isLoading = true
      this.error = null

      try {
        const provider = new ethers.BrowserProvider(window.ethereum)
        const accounts = await provider.send("eth_requestAccounts", [])
        
        this.account = accounts[0]
        
        await this.checkUserRole(this.account)
        
        return true
      } catch (err) {
        this.error = 'Conexión cancelada por el usuario.'
        return false
      } finally {
        this.isLoading = false
      }
    },

    loginAsGuest() {
      this.account = null
      this.userRole = 'guest'
      this.error = null
      this.resetRegistration()
    },
    async refreshRegistration() {
      if (!this.account) return null
      
      try {
        const data = await getRegistrationStatus(this.account)
        if (data) {
          this.registration = {
            status: data.status || 'pending',
            name: data.name || '',
            description: data.description || '',
            nonce: data.nonce !== undefined ? data.nonce : 0
          }
          return this.registration
        }
      } catch (err) {
        console.error('Error al refrescar los datos de registro:', err)
      }
      return null
    },

    async checkUserRole(address) {
      try {
        this.isLoading = true
    
        const adminAddress = await getAdminAddress()
        
        if (address.toLowerCase() === adminAddress.toLowerCase()) {
          this.userRole = 'admin'
          return
        }
        
        // Traemos y guardamos de una vez los datos usando la nueva función
        const reg = await this.refreshRegistration()
        
        if (reg && reg.status === 'authorized') {
          this.userRole = 'creator'
        } 
        else if (reg && (reg.status === 'pending' || reg.status === 'registered')) {
          this.userRole = 'pending'
        }
        else {
          this.userRole = 'guest' // Si es 'archived' o no existe
        }
        
      } catch (err) {
        console.error('Error al verificar el rol:', err)
        this.error = 'Error al verificar el rol con el servidor.'
        this.userRole = 'guest'
        this.resetRegistration()
      } finally {
        this.isLoading = false
      }
    },

    disconnect() {
      this.account = null
      this.userRole = null
      this.resetRegistration()
    },

    resetRegistration() {
      this.registration = {
        status: 'pending',
        name: '',
        description: '',
        nonce: 0
      }
    }
  }
})