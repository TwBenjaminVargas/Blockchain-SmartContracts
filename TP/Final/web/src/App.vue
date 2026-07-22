<template>
  <v-app>
    
    <v-app-bar 
      v-if="route.name !== 'landing'" 
      color="white" 
      elevation="1"
      class="text-slate-dark"
    >
      <v-app-bar-title class="font-weight-bold text-slate-dark">
        CFP Client
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- Estado Conexión MetaMask -->
      <v-chip
        :color="walletStore.account ? 'success' : 'grey-darken-1'"
        variant="flat"
        class="me-4 font-weight-bold text-white"
        size="small"
      >
        {{ walletStore.account ? 'METAMASK CONECTADO' : 'METAMASK DESCONECTADO' }}
      </v-chip>
      <!-- Balance de Tokens BENCOIN -->
      <div 
        v-if="walletStore.account" 
        class="balance-badge me-3 bg-indigo-lighten-5 px-3 py-1 rounded-lg d-flex align-center border border-indigo-lighten-4"
      >
        <v-icon icon="mdi-wallet-outline" size="18" color="indigo-darken-1" class="me-1"></v-icon>
        <span class="text-caption font-weight-bold text-indigo-darken-3 me-1">Balance:</span>
        <span class="text-body-2 font-weight-bold text-slate-dark">
          {{ userBalance }} BEN
        </span>
      </div>
      <!-- Dominio ENS  -->
     <div 
        v-if="walletStore.account && userDomain"
        class="ens-domain-badge me-3 d-flex align-center px-3 py-1 rounded-lg border"
      >
        <v-icon icon="mdi-web" size="16" color="indigo-darken-1" class="me-2"></v-icon>
        <span class="text-caption font-weight-bold text-indigo-darken-3 me-1">
          {{ userDomain }}
        </span>
        <v-btn
          variant="text"
          density="compact"
          icon
          size="small"
          color="indigo-darken-1"
          @click="copyToClipboard(userDomain, 'Dominio copiado al portapapeles')"
        >
          <v-icon size="16">mdi-content-copy</v-icon>
          <v-tooltip activator="parent" location="bottom">Copiar Dominio</v-tooltip>
        </v-btn>
      </div>

      <!-- Dirección Wallet (Muestra recortada, copia la completa) -->
     <div 
        v-if="walletStore.account" 
        class="address-badge me-4 bg-slate-light px-3 py-1 rounded-lg d-flex align-center border"
      >
        <span class="text-body-2 font-weight-medium text-slate-dark me-1">
          {{ truncatedAddress }}
        </span>
        <v-btn
          variant="text"
          density="compact"
          icon
          size="small"
          color="grey-darken-2"
          @click="copyAddressToClipboard"
        >
          <v-icon size="16">mdi-content-copy</v-icon>
          <v-tooltip activator="parent" location="bottom">Copiar Dirección Completa</v-tooltip>
        </v-btn>
      </div>

      <v-btn 
        v-if="!walletStore.account"
        variant="flat" 
        color="indigo-darken-1" 
        class="me-2 font-weight-bold text-white rounded-lg"
        @click="handleConnectFromBar"
      >
        Conectar Wallet
      </v-btn>

      <v-btn 
      v-if="walletStore.account"
      variant="tonal" 
      color="error" 
      class="me-2 font-weight-bold rounded-lg" 
      @click="handleDisconnect"
    >
      Salir
    </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>

    <!-- Feedback -->
    <v-snackbar
      v-model="snackbar.show"
      :timeout="2000"
      color="slate-dark"
      location="bottom right"
      rounded="lg"
    >
      <div class="d-flex align-center text-caption font-weight-medium">
        <v-icon icon="mdi-check-circle-outline" color="success" class="me-2"></v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>

  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useWalletStore } from './stores/wallet'
import { useENSStore } from './stores/ensStore' 
import { useRouter, useRoute } from 'vue-router'
import { reverseResolveAddress } from './services/ens'
import { ethers } from 'ethers'
import { tokenService } from './services/token'

const walletStore = useWalletStore()
const ensStore = useENSStore()
const router = useRouter()
const route = useRoute()
const userDomain = ref('')
const userBalance = ref('0')


// Estado para notificaciones Toast
const snackbar = ref({
  show: false,
  text: ''
})

// Recortar la dirección de la wallet para mostrar
const truncatedAddress = computed(() => {
  if (!walletStore.account) return ''
  return `${walletStore.account.substring(0, 6)}...${walletStore.account.substring(walletStore.account.length - 4)}`
})

// Copiar texto genérico al portapapeles
async function copyToClipboard(text, successMessage) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    snackbar.value.text = successMessage
    snackbar.value.show = true
  } catch (err) {
    console.error('Error al copiar al portapapeles:', err)
  }
}
async function fetchUserBalance(address) {
  if (!address) {
    userBalance.value = '0'
    return
  }
  try {
    const rawBalance = await tokenService.balanceOf(address)
    // Convierte las unidades base (wei/18 decimales) a un valor legible
    const formatted = ethers.formatEther(rawBalance)
    // Redondea a 2 decimales para mostrar en la barra
    userBalance.value = parseFloat(formatted).toFixed(2)
  } catch (error) {
    console.error('Error al obtener el balance de tokens:', error)
    userBalance.value = '0'
  }
}
// Copia la dirección
function copyAddressToClipboard() {
  if (walletStore.account) {
    copyToClipboard(walletStore.account, 'Dirección de Wallet completa copiada')
  }
}

// Escucha cuando walletStore.account cambie
watch(
  () => walletStore.account,
  async (newAccount) => {
    if (newAccount) {
      await fetchUserDomain(newAccount)
      await fetchUserBalance(newAccount)
    } else {
      userDomain.value = ''
    }
  },
  { immediate: true }
)

// Limpia el estado de autenticación y redirige a la Landing
function handleDisconnect() {
  ensStore.resetStore()
  walletStore.disconnect()
  walletStore.userRole = null
  userDomain.value = ''
  router.push({ name: 'landing' })
}

// Lógica de conexión con forzado de selección de cuenta
async function handleConnectFromBar() {
  if (window.ethereum) {
    try {
      await window.ethereum.request({
        method: 'wallet_requestPermissions',
        params: [{ eth_accounts: {} }]
      })
    } catch (e) {
      console.log("El usuario canceló la selección de cuenta")
    }
  }

  const success = await walletStore.connectMetaMask()
  if (success && walletStore.account) {
    await ensStore.refreshStore()
    await walletStore.checkUserRole(walletStore.account)
    await fetchUserDomain(walletStore.account)
    await fetchUserBalance(walletStore.account)
  }
}

async function fetchUserDomain(address) {
  if (!address) {
    userDomain.value = ''
    return
  }
  try {
    const domain = await reverseResolveAddress(address)
    userDomain.value = domain || ''
  } catch (error) {
    console.error("No se pudo obtener el dominio inverso del usuario:", error)
    userDomain.value = ''
  }
}

onMounted(async () => {
  try {
    if (window.ethereum) {
      let accounts = await window.ethereum.request({ method: 'eth_accounts' })
      
      if (!accounts || accounts.length === 0) {
        accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
      }
      
      if (accounts && accounts.length > 0) {
        walletStore.account = accounts[0]
        
        ensStore.refreshStore().catch(console.error)
        fetchUserDomain(accounts[0]).catch(console.error)
        walletStore.checkUserRole(accounts[0]).catch(console.error)
      } else {
        walletStore.account = null
      }
    }
  } catch (err) {
    console.error("Error al detectar/conectar la cuenta en MetaMask:", err)
    walletStore.account = null
  }

  if (window.ethereum) {
    window.ethereum.on('accountsChanged', async (accounts) => {
      if (accounts && accounts.length > 0) {
        walletStore.account = accounts[0]
        userDomain.value = ''
        
        await ensStore.refreshStore()
        await walletStore.checkUserRole(accounts[0])
        await fetchUserDomain(accounts[0])
        await fetchUserBalance(accounts[0])
      } else {
        handleDisconnect()
      }
    })

    window.ethereum.on('chainChanged', () => {
      window.location.reload()
    })
  }
})
</script>

<style>
/* Estilos globales */
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

/* Badge con gradiente suave para el dominio ENS */
.ens-domain-badge {
  background: linear-gradient(135deg, #e0e7ff 0%, #eef2ff 100%);
  border-color: #c7d2fe !important;
  box-shadow: 0 1px 2px rgba(99, 102, 241, 0.05);
}

.address-badge {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}
</style>