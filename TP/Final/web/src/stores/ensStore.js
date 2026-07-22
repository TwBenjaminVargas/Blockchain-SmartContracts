// src/stores/ensStore.js
import { defineStore } from 'pinia'
import { ethers } from 'ethers'
import { getENSAddresses } from '../services/api'
import { FILES, ENSDomains, URL } from '../config/constants'

export const useENSStore = defineStore('ens', {
  state: () => ({
    registryAddress: null,
    resolverAddress: null,
    registrarUsuariosAddress: null,
    registrarLlamadosAddress: null,
    reverseRegistrarAddress: null,

    registryContract: null,
    resolverContract: null,
    registrarUsuariosContract: null,
    registrarLlamadosContract: null,
    reverseRegistrarContract: null,
    
    usuariosSuffix: ENSDomains.usuarios,
    llamadosSuffix: ENSDomains.llamados,
    addrReverseSuffix: ENSDomains.addrReverse,
    
    isInitialized: false,
    loading: false
  }),

  actions: {
    resetStore() {
          this.registryAddress = null
          this.resolverAddress = null
          this.registrarUsuariosAddress = null
          this.registrarLlamadosAddress = null
          this.reverseRegistrarAddress = null
    
          this.registryContract = null
          this.resolverContract = null
          this.registrarUsuariosContract = null
          this.registrarLlamadosContract = null
          this.reverseRegistrarContract = null
    
          this.isInitialized = false
          this.loading = false
          console.log("¡Store de ENS reseteado y vaciado con éxito!")
        },
    async refreshStore() {
      this.loading = true
      try {
        let provider = new ethers.JsonRpcProvider(URL.provider)

        // Si hay cuenta conectada, obtenemos signer para transacciones; si no, usamos provider solo lectura
        let runner = provider

        const baseAddresses = await getENSAddresses()
        this.registryAddress = ethers.getAddress(baseAddresses.registry.trim())
        this.resolverAddress = ethers.getAddress(baseAddresses.resolver.trim())

        const tempRegistry = new ethers.Contract(this.registryAddress, FILES.REGISTRY_ABI, provider)
        const getHash = (dom) => ethers.namehash(dom)

        const [userOwner, llamadosOwner, reverseOwner] = await Promise.all([
          tempRegistry.owner(getHash(this.usuariosSuffix)),
          tempRegistry.owner(getHash(this.llamadosSuffix)),
          tempRegistry.owner(getHash(this.addrReverseSuffix))
        ])

        this.registrarUsuariosAddress = userOwner
        this.registrarLlamadosAddress = llamadosOwner
        this.reverseRegistrarAddress = reverseOwner

        // Instanciar contratos vinculados al runner (Signer o Provider read-only)
        this.registryContract = new ethers.Contract(this.registryAddress, FILES.REGISTRY_ABI, runner)
        this.resolverContract = new ethers.Contract(this.resolverAddress, FILES.RESOLVER_ABI, runner)
        this.registrarUsuariosContract = new ethers.Contract(this.registrarUsuariosAddress, FILES.USUARIOS_REGISTRAR_ABI, runner)
        this.registrarLlamadosContract = new ethers.Contract(this.registrarLlamadosAddress, FILES.LLAMADOS_REGISTRAR_ABI, runner)
        this.reverseRegistrarContract = new ethers.Contract(this.reverseRegistrarAddress, FILES.REVERSE_REGISTRAR_ABI, runner)

        this.isInitialized = true
      } catch (error) {
        console.error("Error inicializando el Store de ENS:", error)
      } finally {
        this.loading = false
      }
    }
  }
})


