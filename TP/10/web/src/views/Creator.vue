<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div class="profile-header d-flex align-center justify-space-between p-4 mb-6 rounded-xl bg-white border-light elevation-1">
            <div class="d-flex align-center flex-grow-1 min-w-0">
              <v-avatar color="indigo-darken-1" size="64" class="me-4 text-white font-weight-bold shadow-sm">
                {{ creatorData.name ? creatorData.name.charAt(0).toUpperCase() : 'C' }}
              </v-avatar>
              <div class="text-left truncate-container">
                <div class="d-flex align-center">
                  <h3 class="text-h5 font-weight-bold text-slate-dark text-truncate max-w-text">
                    {{ creatorData.name || 'Creador sin Nombre' }}
                  </h3>
                  <v-btn
                    variant="tonal"
                    size="small"
                    color="indigo-darken-1"
                    class="ms-2 edit-btn font-weight-bold rounded-lg px-3"
                    :disabled="!walletStore.account"
                    @click="openEditModal"
                  >
                    <img 
                      :src="ASSETS.pencilIcon" 
                      style="width: 16px; height: 16px;" 
                      class="me-2" 
                      alt="Editar" 
                    />
                    Editar
                  </v-btn>
                </div>
                <div class="text-caption text-mono text-grey-darken-1 text-truncate mb-1">
                  {{ walletStore.account || '0x0000...' }}
                </div>
                <p class="text-body-2 text-slate-medium text-wrap italic-description">
                  {{ creatorData.description || 'Sin descripción provista. ¡Haz clic en el lápiz para añadir una!' }}
                </p>
              </div>
            </div>
          </div>

          <div class="d-flex justify-center mb-6 overflow-x-auto">
            <v-btn-toggle
              v-model="currentTab"
              mandatory
              color="indigo-darken-1"
              variant="text"
              class="custom-toggle"
            >
              <v-btn value="calls" class="font-weight-bold">Llamados Creados</v-btn>
            </v-btn-toggle>
          </div>

          <div class="d-flex align-center justify-space-between mb-6 flex-wrap gap-2">
            <h2 class="text-h4 font-weight-bold text-slate-dark">
              {{ panelTitle }}
            </h2>
            <v-btn
              v-if="currentTab === 'calls'"
              color="indigo-darken-1"
              variant="flat"
              class="font-weight-bold text-white rounded-xl px-4"
              :disabled="!walletStore.account || creatorData.status !== 'authorized'"
              @click="openCreateCallModal"
            >
              Añadir Llamado
            </v-btn>
          </div>

          <div v-if="currentTab === 'calls'" class="flex-grow-1 overflow-y-auto pr-2 text-left">
            
            <div v-if="loadingCalls" class="d-flex flex-column align-center justify-center py-12">
              <v-progress-circular indeterminate color="indigo-darken-1" size="50" width="4" class="mb-4"></v-progress-circular>
              <p class="text-body-1 text-grey-darken-1 font-weight-medium">Buscando convocatorias híbridas...</p>
            </div>

            <div v-else-if="allCalls.length > 0">
              <v-expansion-panels variant="accordion" class="rounded-xl border border-light overflow-hidden">
                <v-expansion-panel
                  v-for="call in allCalls"
                  :key="call.callId"
                  class="call-panel-item"
                  @group:selected="initClosingTimeInput(call)"
                >
                  <v-expansion-panel-title class="py-4">
                    <v-row no-gutters class="align-center w-100 min-w-0">
                      <v-col cols="12" md="8" class="d-flex flex-column text-left min-w-0 pr-4">
                        <div class="d-flex align-center flex-wrap gap-2 mb-2">
                          <span class="text-mono text-body-2 font-weight-bold text-indigo-darken-1 bg-indigo-lighten-5 px-2 py-0.5 rounded">
                            {{ call.callId.substring(0, 10) }}...{{ call.callId.substring(call.callId.length - 4) }}
                          </span>
                          
                          <v-chip
                            v-if="call.isInternal"
                            size="small"
                            color="success"
                            variant="flat"
                            class="font-weight-bold text-caption"
                          >
                            Sincronizado (Local)
                          </v-chip>
                          <v-chip
                            v-else
                            size="small"
                            color="amber-darken-2"
                            variant="flat"
                            class="font-weight-bold text-caption"
                          >
                            Blockchain Pura
                          </v-chip>

                          <v-chip
                            v-if="call.isInternal && call.state"
                            size="small"
                            color="indigo-lighten-1"
                            variant="outlined"
                            class="font-weight-bold text-caption"
                          >
                            {{ call.state }}
                          </v-chip>
                        </div>
                        
                        <div class="text-subtitle-1 font-weight-bold text-slate-dark text-truncate w-100">
                          {{ call.title || 'Convocatoria Externa (Sin metadatos)' }}
                        </div>
                      </v-col>

                      <v-col cols="12" md="4" class="text-md-right mt-2 mt-md-0">
                        <span class="text-body-2 font-weight-medium text-slate-medium">
                          <v-icon icon="mdi-clock-outline" size="16" class="me-1 text-grey-darken-1"></v-icon>
                          Cierre: <strong class="text-slate-dark">{{ formatUnixTimestamp(call.closingTime) }}</strong>
                        </span>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text class="bg-slate-lighten-5 pa-2 text-left">
                    <div class="py-2">
                      <h4 class="text-subtitle-1 font-weight-bold text-slate-dark mb-1">
                        {{ call.title || 'Convocatoria Externa' }}
                      </h4>
                      <p class="text-body-2 text-slate-medium mb-3">
                        {{ call.description || 'Este llamado reside únicamente en los nodos de la Blockchain y no cuenta con metadatos extendidos guardados en la base de datos de la API.' }}
                      </p>
                      
                      <v-divider class="mb-3"></v-divider>
                      
                      <div class="d-flex flex-column gap-1 text-caption text-grey-darken-2 mb-4">
                        <div>
                          <v-icon icon="mdi-file-sign" size="14" class="me-1"></v-icon>
                          <strong>Address: </strong>  
                          <span class="text-mono ms-1 select-all">{{ call.contractAddress || 'No desplegado / 0x00...' }}</span>
                        </div>
                        <div>
                          <v-icon icon="mdi-account-circle" size="14" class="me-1"></v-icon>
                          <strong>Creador (Wallet):</strong>  
                          <span class="text-mono ms-1">{{ call.creator || walletStore.account }}</span>
                        </div>
                        <div>
                          <v-icon icon="mdi-identifier" size="14" class="me-1"></v-icon>
                          <strong>Call ID: </strong>  
                          <span class="text-mono ms-1 select-all">{{ call.callId }}</span>
                        </div>
                      </div>

                      <div v-if="call.isInternal && call.state === 'PENDING'" class="mt-4 border pa-4 rounded-xl bg-white elevation-1">
                        <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">
                          Configuración de Cierre On-Chain
                        </div>
                        
                        <v-row class="align-center" dense>
                          <v-col cols="12" sm="6">
                            <v-text-field
                              v-model="closingInputs[call.callId]"
                              label="Fecha y hora límite de cierre"
                              type="datetime-local"
                              variant="outlined"
                              density="comfortable"
                              color="indigo"
                              hide-details
                              prepend-inner-icon="mdi-calendar-clock"
                            ></v-text-field>
                          </v-col>
                          
                          <v-col cols="12" sm="6" class="text-right mt-2 mt-sm-0">
                            <v-btn
                              color="indigo-darken-1"
                              variant="flat"
                              class="font-weight-bold text-white rounded-lg px-4"
                              :loading="!!loadingOnChain[call.callId]"
                              :disabled="!walletStore.account"
                              @click="handleCreateOnChain(call)"
                            >
                              <img src="/metamask-icon.svg" alt="MetaMask" width="26" height="26" class="me-2" />
                              Crear On-Chain
                            </v-btn>
                          </v-col>
                        </v-row>
                      </div>

                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>

            <div v-else class="text-center py-10 text-grey-darken-1 flex-grow-1 d-flex flex-column justify-center align-center">
              <v-img :src="question_svg" max-width="80" class="mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron llamados para esta cuenta.</p>
              <p class="text-caption text-grey-darken-1">Crea una nueva propuesta en la factoría para verla reflejada aquí.</p>
            </div>

          </div>

        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="createCallModal.show" max-width="550px" persistent>
      <v-form ref="createCallForm" lazy-validation>
        <v-card class="rounded-xl pa-4">
          <v-card-title class="text-h5 font-weight-bold text-slate-dark d-flex align-center">
            <v-icon icon="mdi-plus-circle-outline" color="indigo-darken-1" class="me-2"></v-icon>
            Crear Convocatoria
          </v-card-title>

          <v-card-text class="pt-2">
            <v-text-field
              v-model="createCallModal.form.title"
              label="Título del Llamado"
              variant="outlined"
              color="indigo"
              density="comfortable"
              :rules="titleRules"
              class="mb-2"
            ></v-text-field>
          
            <v-textarea
              v-model="createCallModal.form.description"
              label="Descripción detallada"
              variant="outlined"
              color="indigo"
              density="comfortable"
              rows="4"
              no-resize
              :rules="descriptionRules"
            ></v-textarea>
          </v-card-text>
        
          <v-card-actions class="justify-end gap-2 px-6 pb-4">
            <v-btn 
              variant="text" 
              color="grey-darken-1" 
              class="font-weight-bold" 
              :disabled="createCallModal.loading" 
              @click="createCallModal.show = false"
            >
              Cancelar
            </v-btn>
            <v-btn 
              variant="flat" 
              color="indigo-darken-1" 
              class="font-weight-bold text-white" 
              :loading="createCallModal.loading" 
              @click="handleCreateCall"
            >
              Firmar y Publicar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-form>
    </v-dialog>

    <v-dialog v-model="editModal.show" max-width="500px" persistent>
      <v-card class="rounded-xl pa-4">
        <v-card-title class="text-h5 font-weight-bold text-slate-dark d-flex align-center">
          <v-img :src="pencilIcon" max-width="24" class="me-2"></v-img>
          Editar Perfil
        </v-card-title>
        
        <v-card-text class="pt-2">
          <v-text-field
            v-model="editModal.form.name"
            label="Nombre del Creador"
            variant="outlined"
            color="indigo"
            density="comfortable"
            :rules="[v => !!v || 'El nombre es obligatorio']"
            class="mb-2"
          ></v-text-field>

          <v-textarea
            v-model="editModal.form.description"
            label="Descripción o Biografía"
            variant="outlined"
            color="indigo"
            density="comfortable"
            rows="3"
            no-resize
          ></v-textarea>
        </v-card-text>

        <v-card-actions class="justify-end gap-2 px-6 pb-4">
          <v-btn 
            variant="text" 
            color="grey-darken-1" 
            class="font-weight-bold" 
            :disabled="editModal.loading" 
            @click="editModal.show = false"
          >
            Cancelar
          </v-btn>
          <v-btn 
            variant="flat" 
            color="indigo-darken-1" 
            class="font-weight-bold text-white" 
            :loading="editModal.loading" 
            @click="handleUpdateProfile"
          >
            Guardar y Firmar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      elevation="4"
      location="top right"
      :timeout="4000"
      class="mt-4"
    >
      <div class="d-flex align-center">
        <v-icon :icon="snackbar.color === 'success' ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'" class="me-3" size="22"></v-icon>
        <span class="font-weight-medium text-body-2">{{ snackbar.message }}</span>
      </div>
      <template v-slot:actions>
        <v-btn variant="text" size="small" @click="snackbar.show = false" icon="mdi-close"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ethers } from 'ethers'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { 
  getContractAddress, 
  getRegistrationStatus, 
  updateRegistration,
  getUserCalls,
  createCall
} from '../services/api'
import { createInFactory } from '../services/cfpfactory'

const walletStore = useWalletStore()
const loadingOnChain = ref({})

// Diccionario reactivo para las fechas seleccionadas por cada callId
const closingInputs = ref({})

const backgroundImage = ASSETS.creatorBg
const question_svg = ASSETS.questionIcon
const pencilIcon = ASSETS.pencilIcon
const currentTab = ref('calls')

const createCallForm = ref(null)
const loadingCalls = ref(false)
const localCallsList = ref([])
const externalCallsList = ref([])

const creatorData = ref({
  name: '',
  description: '',
  nonce: 0,
  status: ''
})

const snackbar = ref({
  show: false,
  message: '',
  color: 'error'
})

const editModal = ref({
  show: false,
  loading: false,
  form: {
    name: '',
    description: ''
  }
})

const createCallModal = ref({
  show: false,
  loading: false,
  form: {
    title: '',
    description: ''
  }
})

const panelTitle = computed(() => {
  if (currentTab.value === 'calls') return 'Gestión de Llamados'
  return ''
})

const allCalls = computed(() => {
  const internals = localCallsList.value.map(c => ({ ...c, isInternal: true }))
  const externals = externalCallsList.value.map(c => ({ ...c, isInternal: false }))
  return [...internals, ...externals]
})

function showSnackbar(message, color = 'error') {
  snackbar.value = { show: true, message, color }
}

function formatUnixTimestamp(timestamp) {
  if (!timestamp) return 'No definido / Pendiente on-chain'
  const date = new Date(Number(timestamp) * 1000)
  return date.toLocaleString(navigator.language, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Inicializa el input datetime-local a +30 días por defecto cuando el usuario despliega el panel
function initClosingTimeInput(call) {
  if (call.isInternal && call.state === 'PENDING' && !closingInputs.value[call.callId]) {
    const defaultDate = new Date()
    defaultDate.setDate(defaultDate.getDate() + 30)
    
    // Formatear al formato ISO requerido por datetime-local (YYYY-MM-DDTHH:mm)
    const year = defaultDate.getFullYear()
    const month = String(defaultDate.getMonth() + 1).padStart(2, '0')
    const day = String(defaultDate.getDate()).padStart(2, '0')
    const hours = String(defaultDate.getHours()).padStart(2, '0')
    const minutes = String(defaultDate.getMinutes()).padStart(2, '0')
    
    closingInputs.value[call.callId] = `${year}-${month}-${day}T${hours}:${minutes}`
  }
}

async function fetchUserCallsData() {
  if (!walletStore.account) return
  try {
    loadingCalls.value = true
    const data = await getUserCalls(walletStore.account)
    if (data) {
      localCallsList.value = data.local_calls || []
      externalCallsList.value = data.external_calls || []
    }
  } catch (error) {
    console.error("Error al recuperar llamados:", error)
    showSnackbar("Error al sincronizar el catálogo de convocatorias.")
  } finally {
    loadingCalls.value = false
  }
}

async function fetchCreatorProfile() {
  try {
    if (!walletStore.account) return
    const profile = await getRegistrationStatus(walletStore.account)
    if (profile) {
      creatorData.value = {
        name: profile.name || '',
        description: profile.description || '',
        nonce: profile.nonce !== undefined ? profile.nonce : 0,
        status: profile.status || ''
      }
    }
  } catch (error) {
    console.error("Error al buscar perfil del creador:", error)
    showSnackbar("No se pudo sincronizar el perfil con el servidor.")
  }
}

function openEditModal() {
  editModal.value.form = {
    name: creatorData.value.name,
    description: creatorData.value.description
  }
  editModal.value.show = true
}

function openCreateCallModal() {
  createCallModal.value.form = { title: '', description: '' }
  if (createCallForm.value) createCallForm.value.resetValidation()
  createCallModal.value.show = true
}

async function handleCreateCall() {
  if (!createCallForm.value) return
  const { valid } = await createCallForm.value.validate()
  if (!valid) return

  try {
    createCallModal.value.loading = true
    if (!window.ethereum) throw new Error('MetaMask no está disponible.')

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = parseInt(network.chainId.toString(), 10)

    const factoryAddressResult = await getContractAddress()
    const factoryAddress = typeof factoryAddressResult === 'string' ? factoryAddressResult : factoryAddressResult.address
    if (!factoryAddress) throw new Error('No se pudo resolver el address de la factoría.')
    const checksumContractAddress = ethers.getAddress(factoryAddress.trim())

    const titleStr = createCallModal.value.form.title.trim()
    const descStr = createCallModal.value.form.description.trim()

    const titleBytes = ethers.toUtf8Bytes(titleStr)
    const descBytes = ethers.toUtf8Bytes(descStr)
    const rlpEncoded = ethers.encodeRlp([titleBytes, descBytes]) 
    const calculatedCallId = ethers.keccak256(rlpEncoded)

    const domain = {
      name: "CFP API",
      version: "1",
      chainId: chainId,
      verifyingContract: checksumContractAddress
    }

    const types = {
      CreateRequest: [
        { name: "operation", type: "string" },
        { name: "contract", type: "address" },
        { name: "callId", type: "bytes32" }
      ]
    }

    const message = {
      operation: "create",
      contract: checksumContractAddress,
      callId: calculatedCallId
    }

    console.log("%c[Cripto] Solicitando firma para CreateRequest (EIP-712)...", "color: #10b981; font-weight: bold;", message)
    
    const signature = await signer.signTypedData(domain, types, message)

    const payload = {
      callId: calculatedCallId,
      title: titleStr,
      description: descStr,
      signature: signature
    }

    await createCall(payload)

    showSnackbar("¡Convocatoria creada con éxito en estado PENDING!", "success")
    createCallModal.value.show = false
    await fetchUserCallsData()

  } catch (error) {
    console.error("Error al procesar la creación de la convocatoria:", error)
    let alertMsg = 'Ocurrió un error al procesar el llamado.'
    if (error.response && error.response.data && error.response.data.message) {
      alertMsg = `Error del servidor: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      alertMsg = 'Firma rechazada en MetaMask.'
    } else if (error.message) {
      alertMsg = error.message
    }
    showSnackbar(alertMsg)
  } finally {
    createCallModal.value.loading = false
  }
}

async function handleUpdateProfile() {
  if (!editModal.value.form.name.trim()) {
    showSnackbar("El nombre no puede estar vacío.")
    return
  }
  try {
    editModal.value.loading = true
    if (!window.ethereum) throw new Error('MetaMask no está disponible.')

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = parseInt(network.chainId.toString(), 10)

    const factoryAddressResult = await getContractAddress()
    const factoryAddress = typeof factoryAddressResult === 'string' ? factoryAddressResult : factoryAddressResult.address
    const checksumContractAddress = ethers.getAddress(factoryAddress.trim())

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

    const message = {
      operation: "update",
      contract: checksumContractAddress,
      nonce: creatorData.value.nonce,
      name: editModal.value.form.name
    }

    const signature = await signer.signTypedData(domain, types, message)

    const payload = {
      name: editModal.value.form.name,
      description: editModal.value.form.description,
      signature: signature
    }

    await updateRegistration(walletStore.account, payload)
    showSnackbar("¡Perfil actualizado con éxito!", "success")
    editModal.value.show = false
    await fetchCreatorProfile()
  } catch (error) {
    console.error("Error al actualizar perfil:", error)
    let alertMsg = 'Problema al actualizar perfil.'
    if (error.response && error.response.data && error.response.data.message) {
      alertMsg = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      alertMsg = 'Firma denegada.'
    }
    showSnackbar(alertMsg)
  } finally {
    editModal.value.loading = false
  }
}

const getByteSize = (str) => {
  if (!str) return 0
  return new TextEncoder().encode(str).length
}

const titleRules = [
  v => !!v || 'El título es obligatorio.',
  v => getByteSize(v) <= 512 || `El título supera el límite permitido (${getByteSize(v)}/512 bytes en UTF-8).`
]

const descriptionRules = [
  v => !!v || 'La descripción es obligatoria.',
  v => getByteSize(v) <= 4096 || `La descripción supera el límite permitido (${getByteSize(v)}/4096 bytes en UTF-8).`
]

watch(() => walletStore.account, (newAcc) => {
  if (newAcc) {
    fetchCreatorProfile()
    fetchUserCallsData()
  }
})

async function handleCreateOnChain(call) {
  if (!call.callId) {
    showSnackbar("El identificador del llamado no es válido.")
    return
  }

  // Extraer e interpretar el valor del input del usuario
  const userInput = closingInputs.value[call.callId]
  if (!userInput) {
    showSnackbar("Por favor, selecciona una fecha y hora de cierre válida.")
    return
  }

  const selectedDate = new Date(userInput)
  const closingTimestamp = Math.floor(selectedDate.getTime() / 1000)

  // Validación rápida: que no esté en el pasado
  if (closingTimestamp <= Math.floor(Date.now() / 1000)) {
    showSnackbar("La fecha de cierre debe ser mayor al tiempo actual.")
    return
  }

  try {
    loadingOnChain.value[call.callId] = true

    console.log(`[On-Chain] Enviando a Blockchain -> callId: ${call.callId}, closingTime seleccionado: ${closingTimestamp}`)

    // Ejecución contra MetaMask y la Blockchain
    const receipt = await createInFactory(call.callId, closingTimestamp)
    console.log("[On-Chain] Transacción confirmada con éxito:", receipt)

    showSnackbar("¡Transacción confirmada! Refrescando catálogo en 3 segundos...", "success")
    
    // REQUISITO: Esperar 3 segundos (3000ms) antes de realizar el refresco de los llamados
    setTimeout(async () => {
      await fetchUserCallsData()
      // Limpiar el input local del diccionario una vez procesado
      delete closingInputs.value[call.callId]
    }, 3000)

  } catch (error) {
    console.error("Error al ejecutar create on-chain:", error)
    let alertMsg = 'Ocurrió un error al enviar la transacción a la Blockchain.'
    
    if (error.code === 'ACTION_REJECTED') {
      alertMsg = 'Firma rechazada en MetaMask por el usuario.'
    } else if (error.message && error.message.includes('El llamado ya existe')) {
      alertMsg = 'Error: El llamado ya se encuentra registrado en el Smart Contract.'
    } else if (error.message && error.message.includes('No autorizado')) {
      alertMsg = 'Error: Tu wallet no cuenta con autorización en el Smart Contract.'
    } else if (error.message) {
      alertMsg = error.message
    }
    
    showSnackbar(alertMsg)
  } finally {
    loadingOnChain.value[call.callId] = false
  }
}

onMounted(() => {
  fetchCreatorProfile()
  fetchUserCallsData()
})
</script>

<style scoped>
.bg-container {
  overflow: hidden;
  min-height: 100vh;
}

.blur-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  filter: blur(12px) brightness(0.9);
  transform: scale(1.05);
}

.z-index-1 {
  position: relative;
  z-index: 1;
}

.main-panel {
  background-color: rgba(248, 250, 252, 0.92) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  height: 85vh; 
  display: flex;
  flex-direction: column;
}

.profile-header {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 16px;
}

.border-light {
  border: 1px solid #e2e8f0;
}

.truncate-container {
  overflow: hidden;
  width: 100%;
}

.max-w-text {
  max-width: 85%;
}

.italic-description {
  font-style: italic;
  word-wrap: break-word;
  white-space: normal;
}

.edit-btn {
  background-color: #f1f5f9;
  transition: background-color 0.2s;
}
.edit-btn:hover {
  background-color: #e2e8f0;
}

.custom-toggle {
  border: 1px solid #e2e8f0;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 99px !important;
  padding: 4px;
}

.custom-toggle :deep(.v-btn) {
  border-radius: 99px !important;
  text-transform: none;
  letter-spacing: 0;
}

.text-slate-dark {
  color: #0f172a !important;
}

.text-slate-medium {
  color: #334155 !important;
}

.text-mono {
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
}

.gap-1 {
  gap: 4px;
}
.gap-2 {
  gap: 8px;
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.bg-slate-lighten-5 {
  background-color: #f8fafc !important;
}

.select-all {
  user-select: all;
}

.call-panel-item {
  border-bottom: 1px solid #e2e8f0 !important;
  transition: background-color 0.2s ease;
}
.call-panel-item:hover {
  background-color: rgba(241, 245, 249, 0.4);
}
</style>