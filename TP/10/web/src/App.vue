<template>
  <v-app>
    
    <v-app-bar v-if="walletStore.userRole" color="surface-variant" elevation="2">
      <v-app-bar-title class="font-weight-bold">
        DApp Web3 <span class="text-caption text-primary">({{ walletStore.userRole.toUpperCase() }})</span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <span v-if="walletStore.account" class="text-body-2 me-4 bg-grey-darken-3 pa-2 rounded-lg">
        {{ truncatedAddress }}
      </span>

      <v-btn variant="tonal" color="error" class="me-2" @click="handleDisconnect">
        Disconnect
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
import { useRouter } from 'vue-router'

const walletStore = useWalletStore()
const router = useRouter()

// Propiedad computada para recortar la dirección de la wallet (Ej: 0xf39f...2266)
const truncatedAddress = computed(() => {
  if (!walletStore.account) return ''
  return `${walletStore.account.substring(0, 6)}...${walletStore.account.substring(walletStore.account.length - 4)}`
})

// Función para desconectar y mandar al usuario a la Landing
function handleDisconnect() {
  walletStore.disconnect()
  router.push({ name: 'landing' })
}

// Lógica para escuchar cambios reales en la extensión de MetaMask
onMounted(() => {
  if (window.ethereum) {
    // Si el usuario cambia de cuenta en MetaMask...
    window.ethereum.on('accountsChanged', (accounts) => {
      if (accounts.length > 0) {
        // Actualizamos la cuenta en Pinia y recalculamos su rol de inmediato
        walletStore.account = accounts[0]
        walletStore.checkUserRole(accounts[0])
        
        // Lo redirigimos a su nuevo panel correspondiente
        if (walletStore.userRole === 'admin') router.push({ name: 'admin' })
        else if (walletStore.userRole === 'creator') router.push({ name: 'creator' })
      } else {
        // Si desconecta todas las cuentas de MetaMask, limpiamos la sesión
        handleDisconnect()
      }
    })

    // Si el usuario cambia de red (Ej: de Hardhat a Mainnet) reiniciamos la app
    window.ethereum.on('chainChanged', () => {
      window.location.reload()
    })
  }
})
</script>

<style>
/* Estilos globales para toda la aplicación si los necesitas */
html, body {
  margin: 0;
  padding: 0;
  background-color: #121214;
}
</style>