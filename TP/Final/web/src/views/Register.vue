<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="9" lg="6" class="pa-4">
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <!-- Control del progreso visual -->
          <div v-if="currentStep !== 'evaluation'" class="mb-4">
            <div class="d-flex align-center justify-space-between px-2 mb-2">
              <span class="text-caption font-weight-bold" :class="currentStep === 'domain' ? 'text-indigo' : 'text-grey'">1. Dominio</span>
              <span class="text-caption font-weight-bold" :class="currentStep === 'user' ? 'text-indigo' : 'text-grey'">2. Usuario</span>
              <span class="text-caption font-weight-bold" :class="currentStep === 'blockchain' ? 'text-indigo' : 'text-grey'">3. Blockchain</span>
            </div>
            <v-progress-linear :model-value="progressValue" color="indigo" class="rounded" height="6"></v-progress-linear>
          </div>

          <v-window v-model="currentStep" touchless>
            
            <!-- REGISTRO/VERIFICACIÓN DE DOMINIO -->
            <v-window-item value="domain">
              <div class="text-center mb-6">
                <v-icon icon="mdi-web" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
                <h2 class="text-h5 font-weight-bold text-slate-dark">Elige tu Identidad Web3</h2>
                <p class="text-caption text-grey-darken-1 mt-1">Este subdominio será tu dirección única en la red</p>
              </div>

              <v-form ref="domainFormRef" v-model="isDomainFormValid" @submit.prevent="submitDomainStep">
                <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Tu Dirección ENS (.usuarios.cfp) *</div>
                <v-text-field
                  ref="nicknameRef"
                  v-model="formData.nickname"
                  :rules="rules.nicknameRules"
                  :loading="isCheckingDomain"
                  placeholder="Ej: benjasolana"
                  variant="outlined"
                  density="comfortable"
                  color="indigo"
                  class="mb-4 rounded-lg"
                  bg-color="white"
                  suffix=".usuarios.cfp"
                  persistent-hint
                  :messages="domainMessage"
                  required
                ></v-text-field>

                <v-alert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4 rounded-lg text-caption" @click:close="errorMessage = ''">
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
                  :disabled="!isDomainFormValid || !isDomainValidAndFree || isCheckingDomain"
                >
                  Registrar Dominio
                  <v-icon end icon="mdi-arrow-right"></v-icon>
                </v-btn>
              </v-form>
            </v-window-item>

            <!-- REGISTRO DE DATOS DEL USUARIO (FIRMA DIGITAL) -->
            <v-window-item value="user">
              <div class="text-center mb-6">
                <v-icon icon="mdi-account-card-details-outline" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
                <h2 class="text-h5 font-weight-bold text-slate-dark">Información del Perfil</h2>
                <p class="text-caption text-grey-darken-1 mt-1">Completa los datos para tu postulación en el sistema</p>
                <v-chip size="small" color="indigo-lighten-5" class="text-indigo font-weight-medium mt-2">
                  Dominio: {{ confirmedDomain }}
                </v-chip>
              </div>

              <v-form ref="userFormRef" v-model="isUserFormValid" @submit.prevent="handleSystemRegister">
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

                <v-alert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4 rounded-lg text-caption" @click:close="errorMessage = ''">
                  {{ errorMessage }}
                </v-alert>

                <div class="d-flex gap-2">
                  <v-btn v-if="!hasExistingDomain" variant="outlined" color="grey-darken-1" class="rounded-lg font-weight-bold" size="large" @click="currentStep = 'domain'">
                    Atrás
                  </v-btn>
                  <v-btn
                    type="submit"
                    block
                    size="large"
                    variant="flat"
                    color="indigo-darken-1"
                    class="font-weight-bold text-white rounded-lg flex-grow-1"
                    :loading="uiLoading"
                    :disabled="!isUserFormValid"
                  >
                    <v-icon start icon="mdi-fountain-pen-tip"></v-icon>
                    Firmar y Guardar Perfil
                  </v-btn>
                </div>
              </v-form>
            </v-window-item>

            <!-- REGISTRO EN LA BLOCKCHAIN -->
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
                        <p class="text-body-2 text-indigo-darken-2 font-weight-medium mb-1">
                          Dominio Vinculado: {{ confirmedDomain }}
                        </p>
                        <p class="text-body-2 text-slate-medium mb-0">
                          {{ walletStore.registration.description || 'Sin descripción provista.' }}
                        </p>
                      </div>
                      
                      <v-btn variant="text" color="indigo-darken-1" size="small" icon @click="openEditDialog">
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

                  <v-alert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4 rounded-lg text-caption text-left" @click:close="errorMessage = ''">
                    {{ errorMessage }}
                  </v-alert>

                  <v-btn :loading="contractStore.isLoading || uiLoading" block height="56" color="#1e40af" variant="flat" class="mb-4 font-weight-bold rounded-lg text-white text-button" @click="handleBlockchainRegister">
                    <template #prepend>
                      <img src="/metamask-icon.svg" alt="MetaMask" width="26" height="26" class="me-2" />
                    </template>
                    REGISTRARSE EN EL CONTRATO
                  </v-btn>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- PANTALLA DE EVALUACIÓN -->
            <v-window-item value="evaluation">
              <div class="text-center py-6">
                <img :src="clockIconImage" alt="Evaluando solicitud" class="mb-4 pulse-animation clock-icon-svg" />
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
                      <p class="text-body-2 text-indigo-darken-2 font-weight-medium mb-1">
                        Dominio: {{ confirmedDomain }}
                      </p>
                      <p class="text-body-2 text-slate-medium mb-0">{{ walletStore.registration.description || 'Sin descripción provista.' }}</p>
                    </div>
                    
                    <v-btn variant="tonal" size="small" color="indigo-darken-1" class="ms-2 edit-btn font-weight-bold rounded-lg px-3" :disabled="!walletStore.account" @click="openEditDialog">
                      <img :src="pencilIcon" style="width: 16px; height: 16px;" class="me-2" alt="Editar" /> Editar
                    </v-btn>
                  </div>
                </v-card>

                <v-alert type="info" variant="tonal" color="indigo" class="text-left rounded-lg text-body-2 line-height-relaxed">
                  Tu solicitud de registro on-chain está siendo evaluada. Actualmente te encuentras en estado de registro exitoso en la Blockchain. Podrás acceder a la plataforma completa de creadores una vez que seas autorizado por el dueño de la factoría.
                </v-alert>

                <v-btn block variant="flat" color="grey-lighten-3" class="mt-6 font-weight-bold text-slate-dark rounded-lg" @click="checkStatusAgain" :loading="uiLoading">
                  Reverificar Estado
                </v-btn>
              </div>
            </v-window-item>

          </v-window>

        </v-card>
      </v-col>
    </v-row>

    <!-- Dialogo de edición -->
    <v-dialog v-model="editDialog" max-width="500" persistent>
      <v-card class="rounded-xl pa-4">
        <v-card-title class="text-h6 font-weight-bold text-slate-dark">Editar Postulación</v-card-title>
        <v-card-text class="pt-2">
          <v-form ref="editFormRef" v-model="isEditFormValid">
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Nombre del Solicitante *</div>
            <v-text-field v-model="editData.name" :rules="rules.nameRules" variant="outlined" density="comfortable" color="indigo" class="mb-2 rounded-lg" required></v-text-field>
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción (Opcional)</div>
            <v-textarea v-model="editData.description" :rules="rules.descriptionRules" variant="outlined" density="comfortable" color="indigo" rows="3" no-resize></v-textarea>
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
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { useContractStore } from '../stores/cfpfactory'
import { useRouter } from 'vue-router'
import { registerUser, getContractAddress, updateRegistration } from '../services/api'
import { useENSStore } from '../stores/ensStore'
import { registerUserDomain, isDomainAvailable, reverseResolveAddress } from '../services/ens'

const walletStore = useWalletStore()
const contractStore = useContractStore()
const ensStore = useENSStore()
const router = useRouter()

const backgroundImage = ASSETS.registerBg
const clockIconImage = ASSETS.clockIcon
const pencilIcon = ASSETS.pencilIcon

const domainFormRef = ref(null)
const userFormRef = ref(null)
const nicknameRef = ref(null)
const editFormRef = ref(null)

const isDomainFormValid = ref(false)
const isUserFormValid = ref(false)
const isEditFormValid = ref(false)

const uiLoading = ref(false)
const errorMessage = ref('')
const currentStep = ref('domain') 
const editDialog = ref(false)

const isCheckingDomain = ref(false)
const isDomainValidAndFree = ref(false)
const domainMessage = ref('')
const hasExistingDomain = ref(false) 
const confirmedDomain = ref('')

const formData = ref({
  name: '',
  nickname: '', 
  description: ''
})

const editData = ref({
  name: '',
  description: ''
})

const progressValue = computed(() => {
  if (currentStep.value === 'domain') return 33
  if (currentStep.value === 'user') return 66
  if (currentStep.value === 'blockchain') return 100
  return 0
})

const rules = {
  nameRules: [
    v => !!v || 'El nombre es obligatorio.',
    v => (v && v.trim().length > 0) || 'El nombre no puede estar vacío.',
    v => new Blob([v]).size <= 512 || 'El nombre no puede superar los 512 bytes.'
  ],
  nicknameRules: [
    v => !!v || 'El subdominio es obligatorio.',
    v => /^[a-z0-9-]+$/.test(v) || 'Solo letras minúsculas, números y guiones.',
    v => (v && v.length >= 3) || 'Mínimo 3 caracteres.',
    () => isDomainValidAndFree.value || 'Este subdominio ya está ocupado o verificándose.'
  ],
  descriptionRules: [
    v => !v || v.length <= 300 || 'La descripción no puede superar los 300 caracteres.'
  ]
}

let timeoutId = null
watch(() => formData.value.nickname, (newVal) => {
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

const getStatusColor = computed(() => {
  if (!walletStore.registration || !walletStore.registration.status) return 'grey'
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
    errorMessage.value = ''

    // 1. RESETEO TOTAL DE ESTADO (Evita que se filtren datos de la wallet anterior)
    hasExistingDomain.value = false
    confirmedDomain.value = ''
    isDomainValidAndFree.value = false
    formData.value.nickname = ''
    formData.value.name = ''
    formData.value.description = ''

    const currentAddress = walletStore.account.toLowerCase().trim()
    
    // 2. RESOLUCIÓN REVERSA (La única fuente de verdad para el dominio)
    try {
      const detectedDomain = await reverseResolveAddress(currentAddress)

      // Verificamos si la wallet ya posee un dominio válido del sistema
      if (detectedDomain && detectedDomain.endsWith('.usuarios.cfp')) {
        const isAvailable = await isDomainAvailable(detectedDomain)
        
        // Si NO está disponible, significa que ya está tomado (y le pertenece a esta wallet)
        if (!isAvailable) {
          const label = detectedDomain.replace('.usuarios.cfp', '')
          
          // Sincronizamos las variables del dominio de forma segura
          formData.value.nickname = label
          confirmedDomain.value = detectedDomain
          isDomainValidAndFree.value = true
          hasExistingDomain.value = true
          
          // Saltamos el paso 1 ya que tiene dominio
          currentStep.value = 'user'
        }
      }
    } catch (ensErr) {
      console.warn("No se pudo autodetectar el dominio actual por ENS:", ensErr)
    }

    // 3. CARGA DE DATOS DESDE LA API (Solo para el perfil: Nombre, Descripción y Estado)
    const reg = await walletStore.refreshRegistration()
    if (reg) {
      formData.value.name = reg.name || ''
      formData.value.description = reg.description || ''
      
      // Manejo de la navegación según el estado de la API, respetando si ya hay dominio
      if (reg.name && reg.name.trim() !== '') {
        if (reg.status === 'pending') {
          currentStep.value = 'blockchain'
        } else if (reg.status === 'registered') {
          currentStep.value = 'evaluation'
        }
      }
    } else {
      // Si la API no devuelve registro y tampoco detectamos dominio por ENS, va al paso 1
      if (!hasExistingDomain.value) {
        currentStep.value = 'domain'
      }
    }
  } catch (error) {
    console.error("Error cargando el estado inicial de la postulación:", error)
  } finally {
    uiLoading.value = false
  }
}

// Registro de Dominio en ENS
async function submitDomainStep() {
  if (!isDomainFormValid.value || !isDomainValidAndFree.value) return

  try {
    uiLoading.value = true
    errorMessage.value = ''

    if (!window.ethereum) {
      throw new Error('MetaMask no está disponible en este navegador.')
    }

    const cleanLabel = formData.value.nickname.toLowerCase().trim()
    const targetDomain = `${cleanLabel}.usuarios.cfp`
    
    if (!hasExistingDomain.value) {
      // La ejecución se detiene aquí de forma asíncrona hasta que la blockchain confirme el minado
      await registerUserDomain(cleanLabel)
      confirmedDomain.value = targetDomain
    }
    
    // Solo pasa al paso 2 tras la confirmación exitosa del await anterior
    currentStep.value = 'user'
  } catch (error) {
    console.error(error)
    if (error.code === 'ACTION_REJECTED') {
      errorMessage.value = 'Transacción rechazada en MetaMask.'
    } else {
      errorMessage.value = error.message || 'Error al registrar el dominio en la Blockchain.'
    }
  } finally {
    uiLoading.value = false
  }
}

// Firma Digital y API backend
async function handleSystemRegister() {
  if (!isUserFormValid.value) return

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
      domain: confirmedDomain.value, // Enviamos el dominio confirmado estático
      description: formData.value.description && formData.value.description.trim() !== '' 
        ? formData.value.description.trim() 
        : null
    }

    const response = await registerUser(payload)

    if (response) {
      const freshReg = await walletStore.refreshRegistration()
      if (freshReg && freshReg.status === 'authorized') {
        walletStore.userRole = 'creator'
        router.push({ name: 'creator' })
      } else if (freshReg && freshReg.status === 'registered') {
        currentStep.value = 'evaluation'
      } else {
        currentStep.value = 'blockchain'
      }
    }

  } catch (error) {
    console.error(error)
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      errorMessage.value = 'Firma rechazada en MetaMask.'
    } else {
      errorMessage.value = error.message || 'Ocurrió un error al procesar el registro.'
    }
  } finally {
    uiLoading.value = false
  }
}

// Ejecuta la transacción final de CFP Factory on-chain
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
    if (!window.ethereum) throw new Error('MetaMask no está disponible.')

    const factoryAddress = await getContractAddress()
    const mappedAddress = typeof factoryAddress === 'string' ? factoryAddress : factoryAddress.address

    const { ethers } = await import('ethers')
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    
    const checksumContractAddress = ethers.getAddress(mappedAddress.trim())
    const checksumUserAddress = ethers.getAddress(walletStore.account.trim())

    const domain = {
      name: "CFP API",
      version: "1",
      chainId: Number(network.chainId),
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
      description: editData.value.description && editData.value.description.trim() !== '' ? editData.value.description.trim() : null,
      signature: signature
    }

    await updateRegistration(checksumUserAddress, payload)
    await walletStore.refreshRegistration()
    editDialog.value = false
  } catch (error) {
    errorMessage.value = error.message || 'No se pudo actualizar el perfil.'
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

onMounted(async () => {
  try {
    await loadCurrentRegistrationState()
  } catch (err) {
    console.warn(err)
  }
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
  top: 0; left: 0; width: 100%; height: 100%;
  background-size: cover; background-position: center; background-repeat: no-repeat;
  filter: blur(12px) brightness(0.7); transform: scale(1.05); z-index: 0;
}
.z-index-1 { position: relative; z-index: 1; }
.main-panel {
  background-color: rgba(248, 250, 252, 0.93) !important;
  backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.5);
}
.text-slate-dark { color: #0f172a !important; }
.text-slate-medium { color: #475569 !important; }
.clock-icon-svg {
  width: 76px; height: 76px;
  filter: invert(34%) sepia(87%) saturate(1476%) hue-rotate(214deg) brightness(81%) contrast(85%);
}
.line-height-relaxed { line-height: 1.6 !important; }
.pulse-animation { animation: pulse 2.5s infinite ease-in-out; display: inline-block; }
.gap-2 { gap: 8px; }
@keyframes pulse {
  0% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.06); opacity: 1; }
  100% { transform: scale(1); opacity: 0.85; }
}
</style>