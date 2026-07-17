import { defineStore } from 'pinia'
import { ethers } from 'ethers'
import { getENSAddresses } from '../services/api'
import { FILES, ENSDomains} from '../config/constants'

export const useENSStore = defineStore('ens', {
  state: () => ({
    // Direcciones de contratos
    registryAddress: null,
    resolverAddress: null,
    registrarUsuariosAddress: null,
    registrarLlamadosAddress: null,
    reverseRegistrarAddress: null,
    
    // Instancias de contratos (en memoria)
    registryContract: null,
    resolverContract: null,
    registrarUsuariosContract: null,
    registrarLlamadosContract: null,
    reverseRegistrarContract: null,
    
    //Sufijos de dominios
    usuariosSuffix: ENSDomains.usuarios,
    llamadosSuffix: ENSDomains.llamados,
    addrReverseSuffix: ENSDomains.addrReverse,

    isInitialized: false,
    loading: false
  }),

  actions: {
    async initializeStore() {
      // Si ya está inicializado, evitamos repetir la operación
      if (this.isInitialized) return

      this.loading = true
      try {
        if (!window.ethereum) {
          throw new Error('MetaMask no está disponible.')
        }

        const provider = new ethers.BrowserProvider(window.ethereum)
        const signer = await provider.getSigner()

        // Obtener direcciones base
        const baseAddresses = await getENSAddresses()
        
        this.registryAddress = ethers.getAddress(baseAddresses.registry.trim())
        this.resolverAddress = ethers.getAddress(baseAddresses.resolver.trim())

        // Instanciar temporalmente el Registry para hacer las consultas
        const tempRegistry = new ethers.Contract(this.registryAddress, FILES.REGISTRY_ABI, provider)

        // Resolver owners en paralelo
        console.log("Calculando y consultando las direcciones de los registradores en ENS...")
        
        // Helper interno para namehash
        const getHash = (dom) => ethers.namehash(dom)

        const [userOwner, llamadosOwner, reverseOwner] = await Promise.all([
          tempRegistry.owner(getHash(this.usuariosSuffix)),
          tempRegistry.owner(getHash(this.llamadosSuffix)),
          tempRegistry.owner(getHash(this.addrReverseSuffix))
        ])

        // Guardar las direcciones obtenidas en el estado
        this.registrarUsuariosAddress = userOwner
        this.registrarLlamadosAddress = llamadosOwner
        this.reverseRegistrarAddress = reverseOwner

        // Crear todas las instancias de los contratos conectadas al Signer
        this.registryContract = new ethers.Contract(this.registryAddress, FILES.REGISTRY_ABI, signer)
        this.resolverContract = new ethers.Contract(this.resolverAddress, FILES.RESOLVER_ABI, signer)
        
        this.registrarUsuariosContract = new ethers.Contract(this.registrarUsuariosAddress, FILES.USUARIOS_REGISTRAR_ABI, signer)
        this.registrarLlamadosContract = new ethers.Contract(this.registrarLlamadosAddress, FILES.LLAMADOS_REGISTRAR_ABI, signer)
        this.reverseRegistrarContract = new ethers.Contract(this.reverseRegistrarAddress, FILES.REVERSE_REGISTRAR_ABI, signer)

        this.isInitialized = true
        console.log("¡Store de ENS inicializado con éxito en memoria!")

      } catch (error) {
        console.error("Error inicializando el Store de ENS:", error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})