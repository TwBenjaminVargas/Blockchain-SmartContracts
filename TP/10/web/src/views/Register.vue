<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="10" md="8" lg="5" class="pa-4">
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div v-if="hasSubmittedRegistration" class="text-center py-6">
            <img 
              :src="clockIconImage" 
              alt="Evaluando solicitud" 
              class="mb-4 pulse-animation clock-icon-svg"
            />
            
            <h2 class="text-h5 font-weight-bold text-slate-dark mb-4">Solicitud en Evaluación</h2>
            <v-alert
              type="info"
              variant="tonal"
              color="indigo"
              class="text-left rounded-lg text-body-2 line-height-relaxed"
            >
              Tu solicitud de unirte al sistema ha sido recibida con éxito y actualmente está siendo evaluada por el administrador. Podrás acceder a la plataforma de creadores una vez que seas autorizado en la Blockchain.
            </v-alert>
            <v-btn
              block
              variant="flat"
              color="grey-lighten-3"
              class="mt-6 font-weight-bold text-slate-dark rounded-lg"
              @click="checkStatusAgain"
              :loading="uiLoading"
            >
              Reverificar Estado
            </v-btn>
          </div>

          <div v-else>
            <div class="text-center mb-6">
              <v-icon icon="mdi-account-plus-outline" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
              <h2 class="text-h5 font-weight-bold text-slate-dark">Registro de Creador</h2>
              <p class="text-caption text-grey-darken-1 mt-1">Completa tu perfil para enviar la solicitud de acceso</p>
            </div>

            <v-form ref="formRef" v-model="isFormValid" @submit.prevent="handleRegister">
              <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Nombre del Solicitante *</div>
              <v-text-field
                v-model="formData.name"
                :rules="rules.nameRules"
                placeholder="Ej: Benjamín Solana"
                variant="outlined"
                density="comfortable"
                color="indigo"
                class="mb-2 rounded-lg"
                bg-color="white"
                required
              ></v-text-field>

              <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción (Opcional)</div>
              <v-textarea
                v-model="formData.description"
                :rules="rules.descriptionRules"
                placeholder="Cuéntanos brevemente sobre tu perfil o proyectos..."
                variant="outlined"
                density="comfortable"
                color="indigo"
                rows="3"
                class="mb-4 rounded-lg"
                bg-color="white"
                no-resize
              ></v-textarea>

              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                closable
                class="mb-4 rounded-lg text-caption"
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
                class="font-weight-bold text-white rounded-lg"
                :loading="uiLoading"
                :disabled="!isFormValid"
              >
                <v-icon start icon="mdi-fountain-pen-tip"></v-icon>
                Firmar y Registrarse
              </v-btn>
            </v-form>
          </div>

        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ethers } from 'ethers'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { useRouter } from 'vue-router'
import { getRegistrationStatus, registerUser, getContractAddress } from '../services/api'

const walletStore = useWalletStore()
const router = useRouter()

const backgroundImage = ASSETS.registerBg
const clockIconImage = ASSETS.clockIcon

const formRef = ref(null)
const isFormValid = ref(false)
const uiLoading = ref(false)
const errorMessage = ref('')

const hasSubmittedRegistration = ref(false)
const serverNonce = ref(0)

const formData = ref({
  name: '',
  description: ''
})

const rules = {
  nameRules: [
    v => !!v || 'El nombre es obligatorio.',
    v => (v && v.trim().length > 0) || 'El nombre no puede estar vacío.',
    v => new Blob([v]).size <= 512 || 'El nombre no puede superar los 512 bytes.'
  ],
  descriptionRules: [
    v => !v || v.length <= 300 || 'La descripción no puede superar los 300 caracteres.'
  ]
}

async function loadCurrentRegistrationState() {
  if (!walletStore.account) {
    router.push({ name: 'landing' })
    return
  }

  try {
    uiLoading.value = true
    const registration = await getRegistrationStatus(walletStore.account)
    
    if (registration) {
      serverNonce.value = registration.nonce || 0
      
      if (registration.name && registration.name.trim() !== '' && registration.status !== 'archived') {
        hasSubmittedRegistration.value = true
      }
    }
  } catch (error) {
    console.error('Error al recuperar estado de registro:', error)
  } finally {
    uiLoading.value = false
  }
}

async function handleRegister() {
  if (!isFormValid.value) return

  try {
    uiLoading.value = true
    errorMessage.value = ''

    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const factoryAddress = await getContractAddress()
    if (!factoryAddress) {
      throw new Error('No se pudo recuperar la dirección del contrato desde el servidor.')
    }

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = Number(network.chainId)
  
    const checksumContractAddress = ethers.getAddress(factoryAddress.trim())
    const checksumUserAddress = ethers.getAddress(walletStore.account.trim())

    const domain = {
      name: "CFP API",
      version: "1",
      chainId: chainId,
      verifyingContract: checksumContractAddress
    }

    const types = {
      RegisterRequest: [
        { name: "operation", type: "string" },
        { name: "contract", type: "address" },
        { name: "nonce", type: "uint256" },
        { name: "name", type: "string" }
      ]
    }

    const cleanedName = formData.value.name.trim()
    
    const message = {
      operation: "register",
      contract: checksumContractAddress,
      nonce: Number(serverNonce.value),
      name: cleanedName
    }

    const signature = await signer.signTypedData(domain, types, message)

    const payload = {
      address: checksumUserAddress,
      name: cleanedName,
      signature: signature,
      description: formData.value.description && formData.value.description.trim() !== '' 
        ? formData.value.description.trim() 
        : null
    }

    const response = await registerUser(payload)

    if (response && response.status) {
      await walletStore.checkUserRole(walletStore.account)
      
      if (walletStore.userRole === 'creator') {
        router.push({ name: 'creator' })
      } else {
        hasSubmittedRegistration.value = true
      }
    }

  } catch (error) {
    console.error('Error durante el flujo de registro:', error)
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = `Error: ${error.response.data.message}`
    } else {
      errorMessage.value = error.message || 'Ocurrió un error inesperado al procesar la firma.'
    }
  } finally {
    uiLoading.value = false
  }
}

async function checkStatusAgain() {
  try {
    uiLoading.value = true
    await walletStore.checkUserRole(walletStore.account)
    
    if (walletStore.userRole === 'creator') {
      router.push({ name: 'creator' })
    } else if (walletStore.userRole === 'guest') {
      router.push({ name: 'landing' })
    }
  } catch (error) {
    console.error(error)
  } finally {
    uiLoading.value = false
  }
}

onMounted(() => {
  loadCurrentRegistrationState()
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
  background-repeat: no-repeat;
  filter: blur(12px) brightness(0.7);
  transform: scale(1.05);
  z-index: 0;
}

.z-index-1 {
  position: relative;
  z-index: 1;
}

.main-panel {
  background-color: rgba(248, 250, 252, 0.93) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.text-slate-dark {
  color: #0f172a !important;
}

/* FILTRO CSS PARA DARLE COLOR AL SVG DESDE CÓDIGO (Simula el color indigo-darken-1 #3f51b5) */
.clock-icon-svg {
  width: 76px;
  height: 76px;
  filter: invert(34%) sepia(87%) saturate(1476%) hue-rotate(214deg) brightness(81%) contrast(85%);
}

.line-height-relaxed {
  line-height: 1.6 !important;
}

.pulse-animation {
  animation: pulse 2.5s infinite ease-in-out;
  display: inline-block;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.06); opacity: 1; }
  100% { transform: scale(1); opacity: 0.85; }
}
</style>