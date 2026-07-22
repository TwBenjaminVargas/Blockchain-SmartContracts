<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <!-- Fondo desenfocado -->
    <div class="blur-background" :style="{ backgroundImage: `url(${BACKGROUND_IMAGE})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="9" lg="6" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <!-- Cabecera -->
          <div class="d-flex align-center justify-space-between mb-4">
            <v-btn 
              variant="tonal" 
              icon
              color="indigo-darken-1" 
              class="rounded-lg d-flex align-center justify-center"
              @click="$router.push({ name: 'public' })"
            >
              <img :src="exit_svg" alt="Volver" width="24" height="24" style="opacity: 0.8;" />
            </v-btn>
            <h2 class="text-h5 font-weight-bold text-slate-dark text-center flex-grow-1">
              Mi Billetera
            </h2>
            <div style="width: 48px;"></div>
          </div>

          <!-- Estado de carga inicial -->
          <div v-if="loadingWallet" class="d-flex flex-column align-center justify-center my-8 flex-grow-1">
            <v-progress-circular indeterminate color="indigo-darken-1" size="50"></v-progress-circular>
            <span class="text-caption text-slate-medium mt-2">Cargando balance y datos de red...</span>
          </div>

          <template v-else>
            <!-- Card de Balance Destacado -->
            <v-card variant="flat" class="balance-card pa-6 rounded-xl mb-6 text-center">
                <div class="text-caption text-uppercase font-weight-bold tracking-wide balance-label mb-2">
                    Balance Disponible
                </div>

                <div class="d-flex align-center justify-center gap-2 mb-3">
                    <span class="balance-number">
                    {{ formatTokenAmount(userBalance) }}
                    </span>
                    <v-chip
                    color="indigo-darken-1"
                    variant="flat"
                    size="small"
                    class="font-weight-black elevation-1 px-3"
                    >
                    BEN
                    </v-chip>
                </div>
                
                <!-- Dirección / Dominio ENS -->
                <div v-if="walletStore.account" class="d-flex align-center justify-center gap-1 text-caption text-slate-medium">
                    <strong>Cuenta:</strong>
                    <span class="text-mono font-weight-bold text-indigo-darken-2">
                    {{ userDomain || walletStore.account }}
                    </span>
                    <v-btn
                    icon="mdi-content-copy"
                    variant="text"
                    density="compact"
                    color="indigo-darken-1"
                    title="Copiar Dirección"
                    @click="copyToClipboard(walletStore.account)"
                    ></v-btn>
                </div>
            </v-card>

            <!-- Alerta sin billetera conectada -->
            <v-alert
              v-if="!walletStore.account"
              type="warning"
              variant="tonal"
              class="rounded-xl mb-4 text-caption font-weight-bold"
            >
              Conecta tu cuenta de MetaMask para poder realizar operaciones de compra y venta de tokens.
            </v-alert>

            <!-- Pestañas para Operaciones (Comprar / Vender) -->
            <v-tabs v-model="activeTab" color="indigo-darken-1" align-tabs="center" class="mb-4">
              <v-tab value="buy" class="font-weight-bold">Comprar Tokens</v-tab>
              <v-tab value="sell" class="font-weight-bold">Vender Tokens</v-tab>
            </v-tabs>

            <v-window v-model="activeTab" class="pa-2">
              
              <!-- Pestaña: Comprar Tokens -->
              <v-window-item value="buy">
                <v-form ref="buyFormRef" v-model="isBuyFormValid" @submit.prevent="handleBuyTokens">
                  <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Cantidad a Comprar (BEN) *</div>
                  <v-text-field
                    v-model="buyAmount"
                    type="number"
                    min="0"
                    step="any"
                    placeholder="Ej: 100"
                    variant="outlined"
                    color="indigo-darken-1"
                    class="rounded-lg mb-2"
                    density="comfortable"
                    :rules="[v => !!v || 'La cantidad es requerida', v => v > 0 || 'Debe ser mayor a 0']"
                    :disabled="submittingBuy || !walletStore.account"
                  ></v-text-field>

                  <v-btn
                    type="submit"
                    color="indigo-darken-1"
                    variant="flat"
                    block
                    size="large"
                    class="rounded-lg font-weight-bold text-white shadow-sm mt-2"
                    :loading="submittingBuy"
                    :disabled="!isBuyFormValid || !walletStore.account"
                  >
                    Comprar BEN
                  </v-btn>
                </v-form>
              </v-window-item>

              <!-- Pestaña: Vender Tokens -->
              <v-window-item value="sell">
                <v-form ref="sellFormRef" v-model="isSellFormValid" @submit.prevent="handleSellTokens">
                  <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Cantidad a Vender (BEN) *</div>
                  <v-text-field
                    v-model="sellAmount"
                    type="number"
                    min="0"
                    step="any"
                    placeholder="Ej: 50"
                    variant="outlined"
                    color="indigo-darken-1"
                    class="rounded-lg mb-2"
                    density="comfortable"
                    :rules="[
                      v => !!v || 'La cantidad es requerida', 
                      v => v > 0 || 'Debe ser mayor a 0',
                      v => (Number(v) <= Number(formatTokenAmount(userBalance))) || 'Saldo insuficiente'
                    ]"
                    :disabled="submittingSell || !walletStore.account"
                  ></v-text-field>

                  <v-btn
                    type="submit"
                    color="teal-darken-1"
                    variant="flat"
                    block
                    size="large"
                    class="rounded-lg font-weight-bold text-white shadow-sm mt-2"
                    :loading="submittingSell"
                    :disabled="!isSellFormValid || !walletStore.account"
                  >
                    Vender BEN
                  </v-btn>
                </v-form>
              </v-window-item>

            </v-window>

          </template>

        </v-card>
      </v-col>
    </v-row>

    <!-- Modal de Resultado -->
    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="rounded-xl pa-4 bg-white text-center">
        <v-card-title class="justify-center d-flex flex-column align-center">
          <v-icon 
            :icon="dialog.success ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'" 
            :color="dialog.success ? 'success' : 'error'" 
            size="64" 
            class="mb-2"
          ></v-icon>
          <span class="font-weight-bold text-slate-dark text-h6">Transacción {{ dialog.success ? 'Exitosa' : 'Fallida' }}</span>
        </v-card-title>
        <v-card-text class="text-body-1 text-slate-medium pa-2">
          {{ dialog.message }}
        </v-card-text>
        <v-card-actions class="justify-center mt-4">
          <v-btn color="indigo-darken-1" variant="flat" class="rounded-lg font-weight-bold px-6 text-white" @click="dialog.open = false">
            Entendido
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ethers } from 'ethers'
import { useWalletStore } from '../stores/wallet'
import { tokenService } from '../services/token'
import { reverseResolveAddress } from '../services/ens'
import { ASSETS } from '../config/constants'

const walletStore = useWalletStore()
const exit_svg = ASSETS.exitIcon
const BACKGROUND_IMAGE = ASSETS.callsProposalsBg

// Estados UI
const loadingWallet = ref(true)
const activeTab = ref('buy')

// Balances y ENS
const userBalance = ref('0')
const userDomain = ref('')

// Formularios
const buyFormRef = ref(null)
const sellFormRef = ref(null)
const isBuyFormValid = ref(false)
const isSellFormValid = ref(false)
const buyAmount = ref('')
const sellAmount = ref('')

// Loaders
const submittingBuy = ref(false)
const submittingSell = ref(false)

// Modal Informativo
const dialog = ref({ open: false, success: false, message: '' })

const formatTokenAmount = (amount) => {
  if (!amount || amount === '0') return '0'
  try {
    const formatted = ethers.formatEther(amount.toString())
    const numberVal = parseFloat(formatted)
    
    // Formatea con separador de miles y hasta 2 decimales
    return new Intl.NumberFormat('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(numberVal)
  } catch (e) {
    return amount
  }
}

const fetchWalletData = async () => {
  if (!walletStore.account) {
    userBalance.value = '0'
    userDomain.value = ''
    loadingWallet.value = false
    return
  }

  try {
    loadingWallet.value = true
    
    // Consultar Balance
    const balanceHex = await tokenService.balanceOf(walletStore.account)
    userBalance.value = balanceHex.toString()

    // Resolver ENS
    try {
      userDomain.value = await reverseResolveAddress(walletStore.account)
    } catch (e) {
      console.error("Error al resolver ENS:", e)
    }

  } catch (err) {
    console.error("Error cargando datos de la billetera:", err)
  } finally {
    loadingWallet.value = false
  }
}
const handleSellTokens = async () => {
  if (!sellFormRef.value) return
  const { valid } = await sellFormRef.value.validate()
  if (!valid) return

  try {
    submittingSell.value = true

    await tokenService.sell(sellAmount.value.toString())

    dialog.value = {
      open: true,
      success: true,
      message: `¡Has vendido ${sellAmount.value} BEN exitosamente!`
    }
    sellAmount.value = ''
    await fetchWalletData()
  } catch (error) {
    console.error('Error al vender tokens:', error)
    dialog.value = {
      open: true,
      success: false,
      message: error.message || 'La transacción fue rechazada o falló.'
    }
  } finally {
    submittingSell.value = false
  }
}

const handleBuyTokens = async () => {
  if (!buyFormRef.value) return
  const { valid } = await buyFormRef.value.validate()
  if (!valid) return

  try {
    submittingBuy.value = true

    // Se envía la cantidad de BEN que el usuario desea comprar (ej: "100")
    await tokenService.buy(buyAmount.value.toString())

    dialog.value = {
      open: true,
      success: true,
      message: `¡Has comprado ${buyAmount.value} BEN exitosamente!`
    }
    buyAmount.value = ''
    await fetchWalletData()
  } catch (error) {
    console.error('Error al comprar tokens:', error)
    dialog.value = {
      open: true,
      success: false,
      message: error.message || 'La transacción fue rechazada o falló.'
    }
  } finally {
    submittingBuy.value = false
  }
}
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
  } catch (err) {
    console.error('Error al copiar:', err)
  }
}

watch(() => walletStore.account, () => {
  fetchWalletData()
})

onMounted(() => {
  fetchWalletData()
})
</script>

<style scoped>
.bg-container { min-height: 100vh; overflow: hidden; }
.blur-background { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-size: cover; background-position: center; filter: blur(10px) brightness(0.85); transform: scale(1.05); z-index: 0; }
.z-index-1 { z-index: 1; }
.main-panel { background-color: rgba(248, 250, 252, 0.92) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.6); display: flex; flex-direction: column; }
.bg-slate-light { background-color: #ffffff !important; border: 1px solid #e2e8f0; }
.border-light { border: 1px solid #e2e8f0 !important; }
.text-slate-dark { color: #0f172a !important; }
.text-slate-medium { color: #475569 !important; }
.text-mono { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
.gap-1 { gap: 4px; }
/* Card de Balance con efecto Neumórfico Suave y Borde Luminoso */
.balance-card {
  background: linear-gradient(145deg, #ffffff, #f8fafc) !important;
  border: 1px solid rgba(99, 102, 241, 0.15) !important;
  box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important;
}

.balance-label {
  color: #64748b;
  letter-spacing: 1.5px;
}

/* Número con Degradado de Color y Tipografía Tabular */
.balance-number {
  font-size: 2.75rem;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 50%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 10px rgba(99, 102, 241, 0.15);
}

.gap-2 {
  gap: 8px;
}
</style>