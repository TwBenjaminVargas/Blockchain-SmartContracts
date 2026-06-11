<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="9" lg="6" class="pa-4">
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <v-window v-model="currentStep" touchless>
            
            <v-window-item value="form">
              <div class="text-center mb-6">
                <v-icon icon="mdi-account-plus-outline" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
                <h2 class="text-h5 font-weight-bold text-slate-dark">Registro en el Sistema</h2>
                <p class="text-caption text-grey-darken-1 mt-1">Completa tu perfil para enviar la solicitud de acceso</p>
              </div>

              <v-form ref="formRef" v-model="isFormValid" @submit.prevent="handleSystemRegister">
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
                  class="font-weight-bold text-white rounded-lg mb-6"
                  :loading="uiLoading"
                  :disabled="!isFormValid"
                >
                  <v-icon start icon="mdi-fountain-pen-tip"></v-icon>
                  Firmar y Registrarse
                </v-btn>

                <v-divider class="mb-4"></v-divider>
                <div class="d-flex align-center justify-space-between px-2">
                  <span class="text-caption font-weight-bold text-indigo">Paso 1: Sistema</span>
                  <v-progress-linear color="indigo" model-value="50" class="mx-4 rounded" height="6"></v-progress-linear>
                  <span class="text-caption text-grey">Paso 2: Blockchain</span>
                </div>
              </v-form>
            </v-window-item>

            <v-window-item value="blockchain">
              <v-row dense>
                <v-col cols="12">
                  <v-card variant="outlined" color="indigo-lighten-4" class="bg-indigo-lighten-5 rounded-xl pa-4 mb-4 text-left position-relative">
                    <div class="d-flex justify-space-between align-start">
                      <div>
                        <div class="d-flex align-center gap-2 mb-1">
                          <h3 class="text-subtitle-1 font-weight-bold text-slate-dark">{{ walletStore.registration.name }}</h3>
                          <v-chip :color="getStatusColor" size="x-small" variant="flat" class="font-weight-bold text-uppercase">
                            {{ walletStore.registration.status }}
                          </v-chip>
                        </div>
                        <p class="text-body-2 text-slate-medium mb-0">
                          {{ walletStore.registration.description || 'Sin descripción provista.' }}
                        </p>
                      </div>
                      
                      <v-btn
                        variant="text"
                        color="indigo-darken-1"
                        size="small"
                        icon
                        @click="openEditDialog"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                      </v-btn>
                    </div>
                  </v-card>
                </v-col>

                <v-col cols="12" class="text-center py-4">
                  <v-icon icon="mdi-link-variant" color="indigo" size="40" class="mb-2"></v-icon>
                  <h3 class="text-h6 font-weight-bold text-slate-dark mb-1">Registro en la Blockchain</h3>
                  <p class="text-body-2 text-grey-darken-1 mb-6">Tu solicitud está en el sistema. Ahora debes registrar tu identidad de forma on-chain para que el administrador pueda autorizarte.</p>

                  <v-alert
                    v-if="errorMessage"
                    type="error"
                    variant="tonal"
                    closable
                    class="mb-4 rounded-lg text-caption text-left"
                    @click:close="errorMessage = ''"
                  >
                    {{ errorMessage }}
                  </v-alert>

                  <v-btn
                    :loading="contractStore.isLoading || uiLoading"
                    block
                    height="56"
                    color="#1e40af"
                    variant="flat"
                    class="mb-4 font-weight-bold rounded-lg text-white text-button"
                    @click="handleBlockchainRegister"
                  >
                    <template #prepend>
                      <img src="/metamask-icon.svg" alt="MetaMask" width="26" height="26" class="me-2" />
                    </template>
                    REGISTRARSE EN EL CONTRATO
                  </v-btn>
                </v-col>
              </v-row>
            </v-window-item>

            <v-window-item value="evaluation">
              <div class="text-center py-6">
                <img 
                  :src="clockIconImage" 
                  alt="Evaluando solicitud" 
                  class="mb-4 pulse-animation clock-icon-svg"
                />
                
                <h2 class="text-h5 font-weight-bold text-slate-dark mb-4">Solicitud en Evaluación</h2>
                
                <v-card variant="outlined" color="indigo-lighten-4" class="bg-indigo-lighten-5 rounded-xl pa-4 mb-4 text-left">
                  <div class="d-flex justify-space-between align-start">
                    <div>
                      <div class="d-flex align-center gap-2 mb-1">
                        <h3 class="text-subtitle-1 font-weight-bold text-slate-dark">{{ walletStore.registration.name }}</h3>
                        <v-chip :color="getStatusColor" size="x-small" variant="flat" class="font-weight-bold text-uppercase">
                          {{ walletStore.registration.status }}
                        </v-chip>
                      </div>
                      <p class="text-body-2 text-slate-medium mb-0">
                        {{ walletStore.registration.description || 'Sin descripción provista.' }}
                      </p>
                    </div>
                    
                    <v-btn
                      variant="tonal"
                      size="small"
                      color="indigo-darken-1"
                      class="ms-2 edit-btn font-weight-bold rounded-lg px-3"
                      :disabled="!walletStore.account"
                      @click="openEditDialog"
                    >
                    <img 
                      :src="pencilIcon" 
                      style="width: 16px; height: 16px;" 
                      class="me-2" 
                      alt="Editar" 
                    />
                    Editar
                   </v-btn>
                  </div>
                </v-card>

                <v-alert
                  type="info"
                  variant="tonal"
                  color="indigo"
                  class="text-left rounded-lg text-body-2 line-height-relaxed"
                >
                  Tu solicitud de registro on-chain está siendo evaluada. Actualmente te encuentras en estado de registro exitoso en la Blockchain. Podrás acceder a la plataforma completa de creadores una vez que seas autorizado por el dueño de la factoría.
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
            </v-window-item>

          </v-window>

        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="editDialog" max-width="500" persistent>
      <v-card class="rounded-xl pa-4">
        <v-card-title class="text-h6 font-weight-bold text-slate-dark">Editar Postulación</v-card-title>
        <v-card-text class="pt-2">
          <v-form ref="editFormRef" v-model="isEditFormValid">
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Nombre del Solicitante *</div>
            <v-text-field
              v-model="editData.name"
              :rules="rules.nameRules"
              variant="outlined"
              density="comfortable"
              color="indigo"
              class="mb-2 rounded-lg"
              required
            ></v-text-field>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción (Opcional)</div>
            <v-textarea
              v-model="editData.description"
              :rules="rules.descriptionRules"
              variant="outlined"
              density="comfortable"
              color="indigo"
              rows="3"
              no-resize
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions class="justify-end gap-2 px-6 pb-2">
          <v-btn variant="text" color="grey-darken-1" class="font-weight-bold" @click="editDialog = false">Cancelar</v-btn>
          <v-btn variant="flat" color="indigo-darken-1" class="font-weight-bold text-white rounded-lg" :disabled="!isEditFormValid" :loading="uiLoading" @click="handleUpdateProfile">Guardar Cambios</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { useContractStore } from '../stores/cfpfactory'
import { useRouter } from 'vue-router'
import { registerUser, getContractAddress, updateRegistration } from '../services/api'

const walletStore = useWalletStore()
const contractStore = useContractStore()
const router = useRouter()

const backgroundImage = ASSETS.registerBg
const clockIconImage = ASSETS.clockIcon
const pencilIcon = ASSETS.pencilIcon


const formRef = ref(null)
const editFormRef = ref(null)
const isFormValid = ref(false)
const isEditFormValid = ref(false)
const uiLoading = ref(false)
const errorMessage = ref('')
const currentStep = ref('form')
const editDialog = ref(false)

const formData = ref({
  name: '',
  description: ''
})

const editData = ref({
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

const getStatusColor = computed(() => {
  switch (walletStore.registration.status) {
    case 'pending': return 'warning'
    case 'registered': return 'info'
    case 'authorized': return 'success'
    default: return 'grey'
  }
})

async function loadCurrentRegistrationState() {
  if (!walletStore.account) {
    router.push({ name: 'landing' })
    return
  }

  try {
    uiLoading.value = true
    const reg = await walletStore.refreshRegistration()
    
    if (reg) {
      formData.value.name = reg.name || ''
      formData.value.description = reg.description || ''
      
      if (reg.name && reg.name.trim() !== '') {
        if (reg.status === 'pending') {
          currentStep.value = 'blockchain'
        } else if (reg.status === 'registered') {
          currentStep.value = 'evaluation'
        }
      }
    }
  } catch (error) {
    console.error('Error al recuperar estado de registro:', error)
  } finally {
    uiLoading.value = false
  }
}

async function handleSystemRegister() {
  if (!isFormValid.value) return

  try {
    uiLoading.value = true
    errorMessage.value = ''

    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const factoryAddress = await getContractAddress()
    const mappedAddress = typeof factoryAddress === 'string' ? factoryAddress : factoryAddress.address
    if (!mappedAddress) {
      throw new Error('No se pudo recuperar la dirección del contrato desde el servidor.')
    }

    const { ethers } = await import('ethers')
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = Number(network.chainId)
  
    const checksumContractAddress = ethers.getAddress(mappedAddress.trim())
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
      nonce: Number(walletStore.registration.nonce),
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

    if (response) {
      await walletStore.refreshRegistration()
      currentStep.value = 'blockchain'
    }

  } catch (error) {
    console.error('Error durante el flujo de registro:', error)
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      errorMessage.value = 'Firma rechazada en MetaMask.'
    } else {
      errorMessage.value = error.message || 'Ocurrió un error inesperado al procesar la firma.'
    }
  } finally {
    uiLoading.value = false
  }
}

async function handleBlockchainRegister() {
  try {
    uiLoading.value = true
    errorMessage.value = ''

    await contractStore.registerCreator()
    await walletStore.checkUserRole(walletStore.account)
    
    if (walletStore.userRole === 'creator') {
      router.push({ name: 'creator' })
    } else {
      currentStep.value = 'evaluation'
      await walletStore.refreshRegistration()
    }

  } catch (error) {
    console.error('Error durante la transaccion on-chain:', error)
    errorMessage.value = contractStore.errorMessage || error.message || 'Error en la transacción on-chain.'
  } finally {
    uiLoading.value = false
  }
}

function openEditDialog() {
  editData.value.name = walletStore.registration.name
  editData.value.description = walletStore.registration.description
  editDialog.value = true
}

async function handleUpdateProfile() {
  if (!isEditFormValid.value) return

  try {
    uiLoading.value = true
    errorMessage.value = ''

    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const factoryAddress = await getContractAddress()
    const mappedAddress = typeof factoryAddress === 'string' ? factoryAddress : factoryAddress.address
    if (!mappedAddress) {
      throw new Error('No se pudo recuperar la dirección del contrato desde el servidor.')
    }

    const { ethers } = await import('ethers')
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = Number(network.chainId)
  
    const checksumContractAddress = ethers.getAddress(mappedAddress.trim())
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

    const cleanedName = editData.value.name.trim()

    const message = {
      operation: "update",
      contract: checksumContractAddress,
      nonce: Number(walletStore.registration.nonce),
      name: cleanedName
    }

    const signature = await signer.signTypedData(domain, types, message)

    const payload = {
      name: cleanedName,
      description: editData.value.description && editData.value.description.trim() !== '' 
        ? editData.value.description.trim() 
        : null,
      signature: signature
    }

    await updateRegistration(checksumUserAddress, payload)
    
    await walletStore.refreshRegistration()
    editDialog.value = false

  } catch (error) {
    console.error('Error al actualizar el perfil de postulación:', error)
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      errorMessage.value = 'Firma rechazada en MetaMask.'
    } else {
      errorMessage.value = error.message || 'No se pudo actualizar el perfil en el servidor.'
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
    } else {
      await loadCurrentRegistrationState()
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

.text-slate-medium {
  color: #475569 !important;
}

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

.gap-2 {
  gap: 8px;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.06); opacity: 1; }
  100% { transform: scale(1); opacity: 0.85; }
}
</style>