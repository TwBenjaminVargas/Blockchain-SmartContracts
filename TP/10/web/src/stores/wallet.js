import { defineStore } from 'pinia'
import { ethers } from 'ethers'
import {getAdminAddress, getRegistrationStatus} from '../services/api'

export const useWalletStore = defineStore('wallet', {
  state: () => ({
    account: null,
    userRole: null, // Puede ser: 'admin', 'creator', 'guest'
    isLoading: false,
    error: null
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
        // Solicita acceso a las cuentas de MetaMask
        const provider = new ethers.BrowserProvider(window.ethereum)
        const accounts = await provider.send("eth_requestAccounts", [])
        
        this.account = accounts[0]
        
        // Simulación de asignación de roles según la dirección (Wallet)
        // Aquí interactuarías con tu API o Smart Contract en el futuro
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
    },

    async checkUserRole(address) {
      try {
        this.isLoading = true
    
        const adminAddress = await getAdminAddress()
        
        if (address.toLowerCase() === adminAddress.toLowerCase()) {
          this.userRole = 'admin'
          return
        }
        
        const registration = await getRegistrationStatus(address)
        
        if (registration && registration.status === 'authorized') {
          this.userRole = 'creator'
        } 
        // Si el estado es pending, asignamos el rol 'pending' para redirigir a su interfaz
        else if (registration && registration.status === 'pending' || registration.status === 'registered') {
          this.userRole = 'pending'
        }
        // TODO: Manejar el caso de archived, por ahora se trata igual que guest
        else {
          this.userRole = 'guest' // Si está registered o no existe, queda como invitado/guest
        }
        
      } catch (err) {
        console.error('Error al verificar el rol:', err)
        this.error = 'Error al verificar el rol con el servidor.'
        this.userRole = 'guest' // Fallback seguro a guest ante una falla de red o API
      } finally {
        this.isLoading = false
      }
    },

    disconnect() {
      this.account = null
      this.userRole = null
    }
  }
})