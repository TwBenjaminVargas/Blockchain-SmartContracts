import { ethers } from 'ethers'
import { useENSStore } from '../stores/ensStore'

// Helper Namehash
export function getNamehash(domain) {
  if (!domain) return ethers.ZeroHash
  return ethers.namehash(domain)
}

/**
 * Verifica si un dominio ya tiene dueño en el Registry.
 */
export async function isDomainAvailable(domain) {
  const store = useENSStore()


  try {
    const node = getNamehash(domain)
    const owner = await store.registryContract.owner(node)
    
    return owner === ethers.ZeroAddress
  } catch (error) {
    console.error(`Error verificando disponibilidad del dominio ${domain}:`, error)
    return false 
  }
}

// Resolución Directa (domain -> wallet)
export async function resolveDomain(domain) {
  const store = useENSStore()
  try {
    const node = getNamehash(domain)
    const resolverAddress = await store.registryContract.resolver(node)
    
    if (resolverAddress === ethers.ZeroAddress) return null

    const address = await store.resolverContract.addr(node)
    return address === ethers.ZeroAddress ? null : address
  } catch (error) {
    console.error(`Error resolviendo ${domain}:`, error)
    throw error
  }
}

/**
 * Resolución Inversa (wallet -> domain) utilizando Pinia
 * Traduce una dirección pública al nombre de usuario asignado en la red.
 */
export async function reverseResolveAddress(address) {
  const store = useENSStore()


  try {
    // Formatear la dirección bajo el estándar EIP-181
    const cleanAddress = address.toLowerCase().replace('0x', '')
    const addressLabelHash = ethers.keccak256(ethers.toUtf8Bytes(cleanAddress))
    
    // Nodo base "addr.reverse"
    const addrReverseNode = getNamehash('addr.reverse')
    
    // Unión de nodos
    const finalReverseNode = ethers.solidityPackedKeccak256(
      ['bytes32', 'bytes32'],
      [addrReverseNode, addressLabelHash]
    )

    // Consultamos al resolvedor el nombre guardado para ese nodo inverso
    const domain = await store.resolverContract.name(finalReverseNode)
    console.log(`Dirección ${address} resuelta a dominio: ${domain}`)
    return domain || null
  } catch (error) {
    console.error(`Error en resolución inversa para ${address}:`, error)
    throw error
  }
}

// Registro de Usuario con Validación de Colisión
export async function registerUserDomain(label) {
  const store = useENSStore()

  const rootSuffix = store.usuariosSuffix
  const fullDomain = `${label}${rootSuffix}`

  try {
    const available = await isDomainAvailable(fullDomain)
    if (!available) {
      throw new Error(`El dominio "${fullDomain}" ya está registrado por otro usuario.`)
    }

    const userAddress = await store.registryContract.runner.getAddress()

    console.log(`Iniciando registro para: ${fullDomain}...`)
    
    const txRegister = await store.registrarUsuariosContract.register(label)
    await txRegister.wait()

    console.log(`¡Proceso completado con éxito! ${fullDomain} es ahora el dominio de ${userAddress}`)
    return fullDomain
  } catch (error) {
    console.error("Error en registro de usuario:", error)
    throw error 
  }
}