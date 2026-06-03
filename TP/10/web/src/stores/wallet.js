import { defineStore } from 'pinia'
import { ethers } from 'ethers'

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
        this.checkUserRole(this.account)
        
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

    //TODO update to check role from API
    checkUserRole(address) {
      // Hardcodeamos una dirección de ejemplo para pruebas en Hardhat
      const mockAdminAddress = '0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266'
      
      if (address.toLowerCase() === mockAdminAddress.toLowerCase()) {
        this.userRole = 'admin'
      } else {
        this.userRole = 'creator'
      }
    },

    disconnect() {
      this.account = null
      this.userRole = null
    }
  }
})