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

export async function checkLlamadoAvailability(label) {
  const store = useENSStore()
  const fullDomain = `${label}.${store.llamadosSuffix}`
  const node = getNamehash(fullDomain)
  
  try {
    const userAddress = await store.registryContract.runner.getAddress()
    
    // Consultar el dueño actual en el Registry
    const currentOwner = await store.registryContract.owner(node)
    
    // Caso A: Totalmente disponible (Nadie lo ha tomado)
    if (currentOwner === ethers.ZeroAddress) {
      return { available: true, reason: 'available', fullDomain }
    }
    
    // Caso B: Tomado por otra persona
    if (currentOwner.toLowerCase() !== userAddress.toLowerCase()) {
      return { available: false, reason: 'taken', fullDomain }
    }
    
    // Caso C: Es del usuario actual. Validamos si tiene un registro funcional (Resolver)
    const resolverAddress = await store.registryContract.resolver(node)
    if (resolverAddress === ethers.ZeroAddress) {
      // El usuario es dueño pero no tiene resolver apuntado
      return { available: true, reason: 'propietary', fullDomain }
    }
    
    // Caso D: El dominio ya está completamente asignado y en uso por un llamado activo del usuario
    return { available: false, reason: 'assigned', fullDomain }

  } catch (error) {
    console.error("Error en la verificación inteligente de disponibilidad:", error)
    return { available: false, reason: 'error', fullDomain }
  }
}

/**
 * Realiza el registro on-chain invocando al contrato registrarLlamadosContract.
 */
export async function registerLlamadoDomain(label) {
  const store = useENSStore()
  const fullDomain = `${label}.${store.llamadosSuffix}`

  try {
    const status = await checkLlamadoAvailability(label)
    if (!status.available) {
      throw new Error(`El dominio ${fullDomain} no está disponible para registro.`)
    }

    // Si la razón es 'propietary', saltamos el registro on-chain
    // porque ya gastó gas en el pasado y es dueño en el Registry.
    if (status.reason === 'propietary') {
      console.log(`%c[ENS] El dominio ${fullDomain} ya es tuyo en el Registry. Saltando tx de registro...`, "color: #fbbf24;")
      return fullDomain
    }

    console.log(`[ENS] Registrando subdominio de llamado: ${label} -> ${fullDomain}`)
    
    // Llamada al método 'register' del Smart Contract de llamados
    const tx = await store.registrarLlamadosContract.register(label)
    await tx.wait()
    
    console.log(`[ENS] ¡Dominio de llamado registrado exitosamente!`)
    return fullDomain
  } catch (error) {
    console.error("Error al registrar el dominio del llamado en ENS:", error)
    throw error
  }
}

export async function setupLlamadoRecords(label, targetContract) {
  const store = useENSStore()
  try {
    console.log(`[ENS] Configurando records para subdominio: ${label} -> Contrato: ${targetContract}`)
    
    const tx = await store.registrarLlamadosContract.setupRecords(label, targetContract)
    await tx.wait()
    
    console.log(`[ENS] ¡Registros vinculados en Blockchain con éxito!`)
    return true
  } catch (error) {
    console.error("Error al ejecutar setupRecords en ENS:", error)
    throw error
  }
}