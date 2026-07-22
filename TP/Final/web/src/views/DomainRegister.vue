<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <!-- Fondo con efecto difuminado -->
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="10" md="8" lg="5" class="pa-4">
        
        <v-card class="main-panel pa-8 rounded-xl mx-auto" elevation="6">
          
          <!-- Encabezado -->
          <div class="text-center mb-6">
            <v-avatar color="indigo-lighten-5" size="64" class="mb-3 border-indigo">
                <v-icon icon="mdi-account-badge-outline" size="32" color="indigo-darken-1"></v-icon>
            </v-avatar>
            <h1 class="text-h5 font-weight-bold text-slate-dark mb-1">
              Registro de Dominio de Usuario
            </h1>
            <p class="text-body-2 text-slate-medium">
              Obtén tu dirección ENS exclusiva (.usuarios.cfp)
            </p>
          </div>

          <!-- EL USUARIO YA POSEE UN DOMINIO ASIGNADO -->
          <v-slide-y-transition>
            <div v-if="hasExistingDomain" class="text-center">
              <v-card color="indigo-lighten-5" variant="flat" class="pa-6 rounded-xl border-indigo mb-4 text-center">
                <v-icon icon="mdi-check-decagram" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
                <div class="text-caption font-weight-bold text-indigo-darken-3 text-uppercase">
                  Ya cuentas con un dominio asignado
                </div>
                <div class="text-h6 font-weight-bold text-slate-dark mt-1 text-mono">
                  {{ userDomain }}
                </div>
                <p class="text-caption text-slate-medium mt-2 mb-0">
                  Esta billetera ya está vinculada a una identidad activa en la red ENS.
                </p>
              </v-card>

              <v-btn
                variant="outlined"
                color="indigo-darken-1"
                class="font-weight-bold rounded-lg"
                @click="copyToClipboard(userDomain, 'Dominio')"
              >
                <v-icon icon="mdi-content-copy" class="me-2"></v-icon>
                Copiar mi dominio
              </v-btn>
            </div>
          </v-slide-y-transition>

          <!-- EL USUARIO NO TIENE DOMINIO Y PUEDE REGISTRAR UNO -->
          <v-form
            v-if="!hasExistingDomain"
            ref="domainFormRef"
            v-model="isDomainFormValid"
            @submit.prevent="handleRegisterDomain"
          >
            <v-card variant="outlined" class="pa-6 rounded-xl bg-white border-light mb-6">
              <label class="text-caption font-weight-bold text-indigo-darken-3 d-block mb-2 text-left">
                TU DIRECCIÓN ENS (.usuarios.cfp)
              </label>

              <v-text-field
                ref="nicknameRef"
                v-model="nickname"
                :rules="nicknameRules"
                :loading="isCheckingDomain"
                placeholder="ej: benjasolana"
                variant="outlined"
                density="comfortable"
                color="indigo"
                class="mb-2 rounded-lg"
                bg-color="white"
                suffix=".usuarios.cfp"
                persistent-hint
                :messages="domainMessage"
                :disabled="loading || !walletStore.account"
                clearable
              ></v-text-field>

              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                closable
                class="mt-3 rounded-lg text-caption text-left"
                @click:close="errorMessage = ''"
              >
                {{ errorMessage }}
              </v-alert>

              <v-btn
                type="submit"
                block
                size="large"
                variant="flat"
                color="indigo-darken-1"
                class="font-weight-bold text-white rounded-lg mt-4"
                :loading="loading"
                :disabled="!isDomainFormValid || !isDomainValidAndFree || isCheckingDomain || !walletStore.account"
              >
                <v-icon start icon="mdi-web"></v-icon>
                Registrar Mi Dominio
              </v-btn>
            </v-card>
          </v-form>

          <!-- Advertencia si la billetera no está conectada -->
          <v-alert
            v-if="!walletStore.account"
            type="warning"
            variant="tonal"
            class="mt-4 rounded-lg text-caption text-left"
          >
            Debes conectar tu billetera MetaMask para consultar o registrar un dominio de usuario.
          </v-alert>

        </v-card>
      </v-col>
    </v-row>

    <!-- Feedback Toast -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      elevation="4"
      location="top right"
      :timeout="4000"
    >
      <div class="d-flex align-center">
        <v-icon
          :icon="snackbar.color === 'success' ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'"
          class="me-3"
          size="22"
        ></v-icon>
        <span class="font-weight-medium text-body-2">{{ snackbar.message }}</span>
      </div>
      <template #actions>
        <v-btn variant="text" size="small" icon="mdi-close" @click="snackbar.show = false"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { registerUserDomain, isDomainAvailable, reverseResolveAddress } from '../services/ens'

const walletStore = useWalletStore()
const backgroundImage = ASSETS.registerBg

const domainFormRef = ref(null)
const nicknameRef = ref(null)

const nickname = ref('')
const isDomainFormValid = ref(false)
const isCheckingDomain = ref(false)
const isDomainValidAndFree = ref(false)
const domainMessage = ref('')
const loading = ref(false)
const errorMessage = ref('')

const hasExistingDomain = ref(false)
const userDomain = ref('')

const snackbar = ref({
  show: false,
  message: '',
  color: 'error'
})

const nicknameRules = [
  v => !!v || 'El subdominio es obligatorio.',
  v => /^[a-z0-9-]+$/.test(v || '') || 'Solo letras minúsculas, números y guiones.',
  v => (v && v.length >= 3) || 'Mínimo 3 caracteres.',
  () => isDomainValidAndFree.value || 'Este subdominio no está disponible.'
]

function showSnackbar(message, color = 'error') {
  snackbar.value = { show: true, message, color }
}

async function copyToClipboard(text, label) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    showSnackbar(`¡${label} copiado al portapapeles!`, 'success')
  } catch (err) {
    showSnackbar('No se pudo copiar el elemento.')
  }
}

// Escuchador de escritura para verificar disponibilidad del subdominio con Debounce
let timeoutId = null
watch(nickname, (newVal) => {
  if (hasExistingDomain.value) return

  isDomainValidAndFree.value = false
  domainMessage.value = ''
  
  if (!newVal || newVal.length < 3 || !/^[a-z0-9-]+$/.test(newVal)) {
    return
  }

  if (timeoutId) clearTimeout(timeoutId)

  isCheckingDomain.value = true
  timeoutId = setTimeout(async () => {
    try {
      const fullDomain = `${newVal.toLowerCase().trim()}.usuarios.cfp`
      const available = await isDomainAvailable(fullDomain)
      
      if (available) {
        isDomainValidAndFree.value = true
        domainMessage.value = `✓ ¡Excelente! ${fullDomain} está disponible.`
      } else {
        isDomainValidAndFree.value = false
        domainMessage.value = `✗ El subdominio ya se encuentra registrado.`
      }

      await nextTick()
      if (nicknameRef.value) {
        nicknameRef.value.validate()
      }
    } catch (e) {
      domainMessage.value = 'Error al comprobar disponibilidad.'
    } finally {
      isCheckingDomain.value = false
    }
  }, 500)
})

// Detección de dominio existente en la wallet mediante Reverse Resolve
async function checkExistingUserDomain() {
  if (!walletStore.account) {
    hasExistingDomain.value = false
    userDomain.value = ''
    return
  }

  try {
    loading.value = true
    const currentAddress = walletStore.account.toLowerCase().trim()
    const detectedDomain = await reverseResolveAddress(currentAddress)

    if (detectedDomain && detectedDomain.endsWith('.usuarios.cfp')) {
      const available = await isDomainAvailable(detectedDomain)
      
      // Si NO está disponible, le pertenece a esta billetera
      if (!available) {
        hasExistingDomain.value = true
        userDomain.value = detectedDomain
        return
      }
    }

    hasExistingDomain.value = false
    userDomain.value = ''
  } catch (err) {
    console.warn("Error al intentar autodetectar dominio del usuario:", err)
    hasExistingDomain.value = false
  } finally {
    loading.value = false
  }
}

// Ejecución del registro en la red ENS
async function handleRegisterDomain() {
  if (!isDomainFormValid.value || !isDomainValidAndFree.value) return

  try {
    loading.value = true
    errorMessage.value = ''

    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const cleanLabel = nickname.value.toLowerCase().trim()
    
    // Registra el subdominio en Blockchain
    await registerUserDomain(cleanLabel)
    
    showSnackbar('¡Dominio registrado con éxito!', 'success')
    
    // Recarga la verificación para mostrar el estado final
    await checkExistingUserDomain()

  } catch (error) {
    console.error("Error al registrar dominio de usuario:", error)
    if (error.code === 'ACTION_REJECTED') {
      errorMessage.value = 'Transacción rechazada en MetaMask.'
    } else {
      errorMessage.value = error.message || 'Error al registrar el dominio en la Blockchain.'
    }
  } finally {
    loading.value = false
  }
}

// Monitorea cambios de billetera
watch(() => walletStore.account, async () => {
  await checkExistingUserDomain()
})

onMounted(async () => {
  await checkExistingUserDomain()
})
</script>

<style scoped>
.bg-container {
  overflow: hidden;
  min-height: 100vh;
  background-color: #1e1e2f;
}

.blur-background {
  position: absolute;
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
  background-size: cover; 
  background-position: center;
  filter: blur(12px) brightness(0.7); 
  transform: scale(1.05); 
  z-index: 0;
}

.z-index-1 { 
  position: relative; 
  z-index: 1; 
}

.main-panel {
  background-color: rgba(248, 250, 252, 0.95) !important;
  backdrop-filter: blur(12px); 
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.border-light {
  border: 1px solid #e2e8f0 !important;
}

.border-indigo {
  border: 2px solid #c7d2fe !important;
}

.text-slate-dark { 
  color: #0f172a !important; 
}

.text-slate-medium { 
  color: #475569 !important; 
}

.text-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>