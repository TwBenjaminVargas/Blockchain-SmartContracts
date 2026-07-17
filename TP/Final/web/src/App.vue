<template>
  <v-app>
    
    <v-app-bar 
      v-if="walletStore.userRole && route.name !== 'landing'" 
      color="white" 
      elevation="1"
      class="text-slate-dark"
    >
      <v-app-bar-title class="font-weight-bold text-slate-dark">
        CFP Client 
        <span class="text-caption text-indigo font-weight-bold ms-1">
          ({{ walletStore.userRole.toUpperCase() }})
        </span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <v-chip
        :color="walletStore.account ? 'success' : 'grey-darken-1'"
        variant="flat"
        class="me-4 font-weight-bold text-white"
        size="small"
      >
        {{ walletStore.account ? 'METAMASK CONECTADO' : 'METAMASK DESCONECTADO' }}
      </v-chip>

      <span v-if="walletStore.account" class="text-body-2 me-4 bg-slate-light pa-2 rounded-lg font-weight-medium text-slate-dark border">
        {{ truncatedAddress }}
      </span>

      <v-btn 
        v-if="!walletStore.account"
        variant="flat" 
        color="indigo-darken-1" 
        class="me-2 font-weight-bold text-white rounded-lg"
        @click="handleConnectFromBar"
      >
        Conectar Wallet
      </v-btn>

      <v-btn variant="tonal" color="error" class="me-2 font-weight-bold rounded-lg" @click="handleDisconnect">
        Salir
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>

  </v-app>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useWalletStore } from './stores/wallet'
import { useENSStore } from './stores/ensStore' 
import { useRouter, useRoute } from 'vue-router'

const walletStore = useWalletStore()
const ensStore = useENSStore()
const router = useRouter()
const route = useRoute()

// Recortar la dirección de la wallet para mostrar (ej: 0xf39f...2266)
const truncatedAddress = computed(() => {
  if (!walletStore.account) return ''
  return `${walletStore.account.substring(0, 6)}...${walletStore.account.substring(walletStore.account.length - 4)}`
})

// Limpia el estado de autenticación y redirige a la Landing
function handleDisconnect() {
  ensStore.resetStore()
  walletStore.disconnect()
  walletStore.userRole = null
  router.push({ name: 'landing' })
}

// Lógica de conexión desde la barra y redirección según rol
async function handleConnectFromBar() {
  const success = await walletStore.connectMetaMask()
  if (success) {
    if (walletStore.userRole === 'admin') router.push({ name: 'admin' })
    else if (walletStore.userRole === 'pending') router.push({ name: 'register' })
    else if (walletStore.userRole === 'creator') router.push({ name: 'creator' })
  }
}

onMounted(async () => {
  // Carga inicial: Cuando se refresca o entra por primera vez a la página
  try {
    if (window.ethereum) {
      const accounts = await window.ethereum.request({ method: 'eth_accounts' })
      if (accounts.length > 0) {
        walletStore.account = accounts[0]
        await ensStore.refreshStore()
        await walletStore.checkUserRole(accounts[0])
      }
    }
  } catch (err) {
    console.error("Error en inicialización al cargar la página:", err)
  }

  //Escucha dinámica: Cuando el usuario cambia de cuenta activamente en MetaMask
  if (window.ethereum) {
    window.ethereum.on('accountsChanged', async (accounts) => {
      if (accounts.length > 0) {
        walletStore.account = accounts[0]
        
        console.log("Cambio de cuenta detectado. Reseteando estados y redirigiendo a la página inicial...")
        
        // Ejecuta el refresco total de contratos con el nuevo Signer
        await ensStore.refreshStore()
        
        // Verifica el rol de la nueva cuenta para tener el estado listo
        await walletStore.checkUserRole(accounts[0])
        
        // Redirige forzosamente a la landing/primera página
        router.push({ name: 'landing' }) 
        
      } else {
        // Si desconecta todas las cuentas de MetaMask
        handleDisconnect()
      }
    })

    // Recarga estructural en caso de cambio de red blockchain
    window.ethereum.on('chainChanged', () => {
      window.location.reload()
    })
  }
})
</script>

<style>
/* Estilos globales y utilidades de color/borde */
html, body {
  margin: 0;
  padding: 0;
  background-color: #f8fafc;
}

.text-slate-dark {
  color: #0f172a !important;
}

.bg-slate-light {
  background-color: #f1f5f9 !important;
}

.border {
  border: 1px solid #e2e8f0 !important;
}
</style>