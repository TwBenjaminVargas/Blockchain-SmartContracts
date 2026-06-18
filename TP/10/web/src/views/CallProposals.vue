<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${BACKGROUND_IMAGE})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
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
              Propuestas Registradas
            </h2>
            <div style="width: 48px;"></div>
          </div>

          <div v-if="loadingCall" class="d-flex flex-column align-center justify-center my-8 flex-grow-1">
            <v-progress-circular indeterminate color="indigo-darken-1" size="50"></v-progress-circular>
            <span class="text-caption text-slate-medium mt-2">Cargando datos de la convocatoria...</span>
          </div>

          <template v-else>
            <v-card v-if="callData" variant="flat" class="bg-slate-light pa-4 rounded-xl mb-6 shadow-sm border-light">
              <div class="d-flex align-center mb-2">
                <h3 class="text-h6 font-weight-bold text-slate-dark">{{ callData.title }}</h3>
              </div>
              <p class="text-body-2 text-slate-medium italic-description mb-3">
                {{ callData.description }}
              </p>
              <v-divider class="mb-3"></v-divider>
              <div class="d-flex justify-space-between align-center flex-wrap gap-2">
                <div class="text-caption text-slate-medium">
                  <strong>ID Convocatoria:</strong> <span class="text-mono">{{ callId }}</span>
                </div>
                <v-chip :color="isCallClosed ? 'grey-darken-1' : 'error'" size="small" variant="flat" class="font-weight-bold rounded-lg">
                    {{ isCallClosed ? 'Cerrado' : 'Cierre' }}: {{ formatTimestamp(closingTimeISO) }}
                </v-chip>
              </div>
            </v-card>

            <div class="d-flex justify-space-between align-center mb-4">
              <h4 class="text-subtitle-1 font-weight-bold text-slate-dark">
                Listado de Postulaciones ({{ proposals.length }})
              </h4>
              <v-btn
                v-if="!isCallClosed && !hasRestrictedRole"
                color="indigo-darken-1"
                variant="flat"
                class="rounded-lg font-weight-bold text-white px-4 shadow-sm"
                @click="resetFormAndOpen"
              >
                Añadir Propuesta
              </v-btn>
              <v-chip v-else-if="isCallClosed" color="amber-darken-2" variant="tonal" class="font-weight-bold rounded-lg">
                Convocatoria Finalizada
              </v-chip>
              <v-chip v-else color="grey-darken-2" variant="tonal" class="font-weight-bold rounded-lg">
                Modo Consulta
              </v-chip>
            </div>

            <div v-if="loadingProposals" class="d-flex justify-center my-8 flex-grow-1 align-center">
              <v-progress-circular indeterminate color="indigo-darken-1"></v-progress-circular>
            </div>

            <v-alert 
              v-else-if="proposals.length === 0" 
              type="info" 
              variant="tonal" 
              class="rounded-xl d-flex align-center justify-center my-auto flex-grow-1"
              max-height="120"
            >
              Aún no se han registrado propuestas para esta convocatoria.
            </v-alert>

            <v-scrollbar v-else class="proposals-scroll-containerpe pe-1">
              <v-expansion-panels variant="accordion">
                <v-expansion-panel
                  v-for="proposal in proposals"
                  :key="proposal.proposalId"
                  class="proposal-row mb-3 rounded-xl overflow-hidden"
                  elevation="1"
                >
                  <v-expansion-panel-title class="font-weight-bold text-slate-dark py-4">
                    <div class="d-flex align-center justify-space-between w-100 pr-4">
                      <div class="d-flex align-center">
                        <span>{{ proposal.title }}</span>
                      </div>
                      
                      <v-chip
                        :color="matchState(proposal.state, 'delivered') ? 'success' : (matchState(proposal.state, 'pending') ? 'grey-darken-1' : 'warning')"
                        size="small"
                        variant="flat"
                        class="font-weight-bold rounded-lg"
                      >
                        {{ matchState(proposal.state, 'delivered') ? 'Archivos Recibidos' : (matchState(proposal.state, 'pending') ? 'Pendiente' : 'Registrada') }}
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>

                  <v-expansion-panel-text class="text-slate-medium pt-3 bg-slate-light-flat">
                    <div class="mb-3">
                      <strong>Descripción del Oferente:</strong>
                      <p class="text-body-2 mt-1 text-slate-dark">{{ proposal.description }}</p>
                    </div>
                    
                    <div class="mb-2 text-caption">
                      <strong>Raíz de Merkle (Proposal ID):</strong> 
                      <span class="text-mono text-indigo-darken-1 d-block text-truncate">{{ proposal.proposalId }}</span>
                    </div>

                    <div v-if="proposal.blockchainEvidence?.registrationTx" class="mb-2 text-caption">
                      <strong>Tx Registro:</strong> 
                      <span class="text-mono text-slate-dark d-block text-truncate">{{ proposal.blockchainEvidence.registrationTx }}</span>
                    </div>

                    <div class="d-flex justify-end gap-2 border-top pt-3">
                      
                      <template v-if="matchState(proposal.state, 'delivered')">
                        <v-btn
                          color="indigo-darken-1"
                          variant="flat"
                          class="rounded-lg font-weight-bold text-white shadow-sm"
                          :loading="downloadingZipId === proposal.proposalId"
                          @click="downloadPhysicalFiles(proposal.proposalId)"
                        >
                          Descargar ZIP
                        </v-btn>

                        <v-btn
                          color="success"
                          variant="outlined"
                          class="rounded-lg font-weight-bold"
                          :loading="downloadingReceiptId === proposal.proposalId"
                          @click="downloadFinalReceipt(proposal.proposalId)"
                        >
                          Recibo Post-Cierre
                        </v-btn>
                      </template>

                      <template v-else-if="hasRestrictedRole">
                        <span class="text-caption text-slate-medium my-auto italic">Vista de solo lectura para administradores/creadores</span>
                      </template>

                      <template v-else-if="isCallClosed && (matchState(proposal.state, 'created') || matchState(proposal.state, 'initial') || !proposal.state)">
                        <v-btn
                          color="warning"
                          variant="flat"
                          class="rounded-lg font-weight-bold text-white shadow-sm"
                          @click="openPostClosingModal(proposal)"
                        >
                          Entrega Post-Cierre
                        </v-btn>
                      </template>

                      <template v-else-if="matchState(proposal.state, 'created') || matchState(proposal.state, 'initial') || !proposal.state">
                        <input
                          type="file"
                          :id="'receipt-input-' + proposal.proposalId"
                          style="display: none"
                          accept=".json"
                          @change="handleReceiptUpload($event, proposal.proposalId)"
                        />
                        
                        <v-btn
                          color="indigo-darken-1"
                          variant="outlined"
                          class="rounded-lg font-weight-bold"
                          :loading="verifyingId === proposal.proposalId"
                          @click="triggerReceiptSelection(proposal.proposalId)"
                        >
                          Verificar Recibo
                        </v-btn>

                        <v-btn
                          color="secondary"
                          variant="outlined"
                          class="rounded-lg font-weight-bold border-light text-slate-dark"
                          @click="downloadReceipt(proposal.proposalId)"
                        >
                          Descargar Recibo Inicial
                        </v-btn>
                      </template>

                      <template v-else-if="matchState(proposal.state, 'pending')">
                        <span class="text-caption text-slate-medium my-auto italic">Procesando entrega en blockchain...</span>
                      </template>

                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-scrollbar>
          </template>

        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialogOpen" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4 bg-white panel-modal shadow-lg">
        <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6">
          <div class="d-flex align-center">
            Nueva Propuesta
          </div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="dialogOpen = false" :disabled="submitting"></v-btn>
        </v-card-title>
        <v-divider class="my-2"></v-divider>
        <v-card-text class="pa-2">
          <v-form ref="formRef" v-model="isFormValid" lazy-validation>
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Título de la propuesta *</div>
            <v-text-field
              v-model="formProposal.title"
              :rules="[v => !!v || 'El título es obligatorio', v => v.length <= 150 || 'El título no puede superar los 150 caracteres']"
              placeholder="Ej: Desarrollo de Infraestructura Descentralizada"
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-2"
              density="comfortable"
              :disabled="submitting"
            ></v-text-field>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción Corta *</div>
            <v-textarea
              v-model="formProposal.description"
              :rules="[v => !!v || 'La descripción es obligatoria', v => v.length <= 1000 || 'La descripción no puede superar los 1000 caracteres']"
              placeholder="Detalla los alcances técnicos resumidos de tu postulación..."
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-4"
              rows="3"
              auto-grow
              density="comfortable"
              :disabled="submitting"
            ></v-textarea>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Archivos Comprobatorios *</div>
            <input type="file" ref="fileInputRef" multiple style="display: none" @change="onFilesSelected" accept=".pdf,.zip,.docx" />
            <div 
              class="drag-drop-zone d-flex flex-column align-center justify-center pa-6 rounded-xl text-center mb-2"
              @dragover.prevent
              @drop.prevent="onFilesDropped"
              :class="{ 'disabled-zone': submitting }"
              style="border: 2px dashed #cbd5e1; cursor: pointer; transition: background 0.2s;"
              @click="$refs.fileInputRef.click()"
            >
              <div class="text-body-2 font-weight-bold text-slate-dark mb-1">Arrastra tus archivos aquí o haz clic para buscar</div>
              <div class="text-caption text-slate-medium mb-3">Formatos permitidos: PDF, ZIP, DOCX (Máx. 10MB c/u)</div>
            </div>

            <div v-if="selectedFilesList.length > 0" class="mb-2">
              <div class="text-caption font-weight-bold text-slate-dark mb-1">Archivos seleccionados ({{ selectedFilesList.length }}):</div>
              <v-sheet max-height="120" class="overflow-y-auto pa-2 border rounded-lg bg-slate-light-flat">
                <div v-for="(fileItem, index) in selectedFilesList" :key="index" class="d-flex align-center justify-space-between text-caption border-bottom py-1">
                  <div class="d-flex align-center text-truncate max-w-70">
                    <span class="text-truncate">{{ fileItem.name }}</span>
                  </div>
                  <div class="d-flex align-center">
                    <span v-if="fileItem.hashing" class="text-orange font-weight-bold me-2 text-xxs">Calculando hash...</span>
                    <span v-else class="text-success font-weight-bold me-2 text-mono text-xxs">✓ {{ fileItem.hash.substring(0,10) }}...</span>
                    <v-btn variant="text" density="compact" color="error" @click.stop="removeFile(index)" :disabled="submitting"></v-btn>
                  </div>
                </div>
              </v-sheet>
            </div>

            <v-alert v-if="localProposalId" type="success" variant="tonal" class="rounded-xl mt-3 pa-2" icon="mdi-shield-check-outline">
              <div class="text-caption font-weight-bold">Proposal ID Calculado Localmente:</div>
              <div class="text-mono text-truncate text-xxs">{{ localProposalId }}</div>
            </v-alert>
            <div v-if="fileError" class="text-caption text-error mb-2 font-weight-bold">{{ fileError }}</div>
          </v-form>
        </v-card-text>
        <v-card-actions class="justify-end pa-2 border-top mt-4">
          <v-btn variant="text" color="slate-medium" class="rounded-lg font-weight-bold px-4" @click="dialogOpen = false" :disabled="submitting">Cancelar</v-btn>
          <v-btn color="indigo-darken-1" variant="flat" class="rounded-lg font-weight-bold px-6 text-white shadow-sm" @click="submitProposal" :loading="submitting" :disabled="selectedFilesList.length === 0 || hashingInProgress">Enviar Propuesta</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="postClosingDialogOpen" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4 bg-white panel-modal shadow-lg">
        <v-card-title class="d-flex align-center justify-space-between text-slate-dark font-weight-bold text-h6">
          <div class="d-flex align-center">
            Entrega Post-Cierre
          </div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="postClosingDialogOpen = false" :disabled="submittingPostClosing"></v-btn>
        </v-card-title>
        <v-divider class="my-2"></v-divider>
        <v-card-text class="pa-2">
          <div class="text-caption text-slate-medium mb-4">La convocatoria ha cerrado. Para consolidar la entrega, debes adjuntar el archivo JSON de tu recibo junto con los archivos originales correspondientes.</div>
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">1. Seleccionar Recibo Original (.json) *</div>
          <v-file-input label="Buscar archivo de recibo" accept=".json" variant="outlined" density="comfortable" color="indigo-darken-1" prepend-icon="mdi-script-text-outline" :disabled="submittingPostClosing" @change="onReceiptFileChanged"></v-file-input>
          <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">2. Cargar Archivos Físicos Originales *</div>
          <v-file-input label="Buscar archivos de la propuesta" multiple accept=".pdf,.zip,.docx" variant="outlined" density="comfortable" color="indigo-darken-1" prepend-icon="mdi-paperclip" :disabled="submittingPostClosing" @change="onPostClosingFilesChanged"></v-file-input>
          <v-alert v-if="postClosingError" type="error" variant="tonal" class="rounded-xl mt-3 pa-2 text-caption font-weight-bold">{{ postClosingError }}</v-alert>
        </v-card-text>
        <v-card-actions class="justify-end pa-2 border-top mt-4">
          <v-btn variant="text" color="slate-medium" class="rounded-lg font-weight-bold px-4" @click="postClosingDialogOpen = false" :disabled="submittingPostClosing">Cancelar</v-btn>
          <v-btn color="warning" variant="flat" class="rounded-lg font-weight-bold px-6 text-white shadow-sm" @click="submitPostClosingData" :loading="submittingPostClosing" :disabled="!postClosingReceiptFile || postClosingFilesList.length === 0">Enviar Archivos</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="verificationDialog.open" max-width="500px">
      <v-card class="rounded-xl pa-4 bg-white text-center">
        <v-card-title class="justify-center d-flex flex-column align-center">
          <v-icon :icon="verificationDialog.success ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'" :color="verificationDialog.success ? 'success' : 'error'" size="64" class="mb-2"></v-icon>
          <span class="font-weight-bold text-slate-dark text-h6">Resultado del Proceso</span>
        </v-card-title>
        <v-card-text class="text-body-1 text-slate-medium pa-2">{{ verificationDialog.message }}</v-card-text>
        <v-card-actions class="justify-center mt-4">
          <v-btn color="indigo-darken-1" variant="flat" class="rounded-lg font-weight-bold px-6 text-white" @click="verificationDialog.open = false">Entendido</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute } from 'vue-router'
import { keccak256 } from 'js-sha3'
import { useWalletStore } from '../stores/wallet'
import { 
  getCallById, 
  getProposalsByCall, 
  getProposalReceipt, 
  getClosingTime, 
  registerProposal as apiRegisterProposal,
  verifyProposalReceipt,
  submitPostClosing,
  downloadProposalFiles,
  getProposalReceiptPostClosing 
} from '../services/api'
import { ASSETS } from '../config/constants'

const route = useRoute()
const walletStore = useWalletStore()
const callId = ref(route.params.callId)
const exit_svg = ASSETS.exitIcon
const BACKGROUND_IMAGE = ASSETS.callsProposalsBg

const formRef = ref(null)
const fileInputRef = ref(null)

const dialogOpen = ref(false)
const loadingCall = ref(true)
const loadingProposals = ref(true)
const submitting = ref(false)
const isFormValid = ref(false)

const downloadingZipId = ref(null)
const downloadingReceiptId = ref(null)

const callData = ref(null)
const proposals = ref([])
const closingTimeISO = ref(null)

const currentTime = ref(new Date())
let clockInterval = null

const formProposal = ref({ title: '', description: '' })
const selectedFilesList = ref([])
const fileError = ref(null)

const verifyingId = ref(null)
const verificationDialog = ref({ open: false, success: false, message: '' })

const postClosingDialogOpen = ref(false)
const submittingPostClosing = ref(false)
const postClosingReceiptFile = ref(null)
const postClosingFilesList = ref([])
const postClosingError = ref(null)
const selectedProposal = ref(null)

const hashingInProgress = computed(() => selectedFilesList.value.some(f => f.hashing))

const isCallClosed = computed(() => {
  if (!closingTimeISO.value) return false
  return currentTime.value > new Date(closingTimeISO.value)
})

const hasRestrictedRole = computed(() => {
  const role = walletStore.userRole?.toLowerCase()
  return role === 'admin' || role === 'creator'
})

const matchState = (currentStatus, targetStatus) => {
  if (currentStatus === undefined || currentStatus === null) return false
  return currentStatus.toString().trim().toLowerCase() === targetStatus.trim().toLowerCase()
}

// --- ARBOL DE MERKLE LOCAL ---
const localProposalId = computed(() => {
  if (!formProposal.value.title || !formProposal.value.description || selectedFilesList.value.length === 0 || hashingInProgress.value) {
    return ''
  }
  try {
    const leavesHex = [
      callId.value.toLowerCase().replace('0x', ''),
      keccak256(formProposal.value.title),
      keccak256(formProposal.value.description),
      ...selectedFilesList.value.map(f => f.hash.toLowerCase().replace('0x', ''))
    ]
    leavesHex.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
    const n = leavesHex.length
    const tree = new Array(2 * n - 1).fill('')
    for (let i = 0; i < n; i++) {
      tree[2 * n - 2 - i] = leavesHex[i]
    }
    const hexToBytes = (hex) => {
      const arr = new Uint8Array(hex.length / 2)
      for (let i = 0; i < arr.length; i++) {
        arr[i] = parseInt(hex.substr(i * 2, 2), 16)
      }
      return arr
    }
    for (let i = n - 2; i >= 0; i--) {
      const leftHex = tree[2 * i + 1]
      const rightHex = tree[2 * i + 2]
      const leftBytes = hexToBytes(leftHex)
      const rightBytes = hexToBytes(rightHex)
      let isLeftSmaller = true
      for (let j = 0; j < Math.min(leftBytes.length, rightBytes.length); j++) {
        if (leftBytes[j] !== rightBytes[j]) {
          isLeftSmaller = leftBytes[j] < rightBytes[j]
          break
        }
      }
      const combinedBytes = new Uint8Array(leftBytes.length + rightBytes.length)
      if (isLeftSmaller) {
        combinedBytes.set(leftBytes, 0)
        combinedBytes.set(rightBytes, leftBytes.length)
      } else {
        combinedBytes.set(rightBytes, 0)
        combinedBytes.set(leftBytes, rightBytes.length)
      }
      tree[i] = keccak256(combinedBytes)
    }
    return '0x' + tree[0].toLowerCase()
  } catch (err) {
    console.error('Error calculando Merkle Root local:', err)
    return ''
  }
})

const downloadPhysicalFiles = async (proposalId) => {
  try {
    downloadingZipId.value = proposalId
    await downloadProposalFiles(proposalId)
  } catch (error) {
    console.error(error)
    alert("No se pudieron descargar los archivos físicos de la propuesta.")
  } finally {
    downloadingZipId.value = null
  }
}

const downloadFinalReceipt = async (proposalId) => {
  try {
    downloadingReceiptId.value = proposalId
    const fullReceiptData = await getProposalReceiptPostClosing(proposalId)
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fullReceiptData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `recibo_definitivo_${proposalId.substring(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (error) {
    console.error(error)
    alert("Error al descargar el recibo post-cierre definitivo.")
  } finally {
    downloadingReceiptId.value = null
  }
}

const formatTimestamp = (value) => {
  if (!value) return 'Sin fecha'
  const date = typeof value === 'string' ? new Date(value) : new Date(value * 1000)
  if (isNaN(date.getTime())) return 'Fecha inválida'
  return date.toLocaleString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const loadCallDetails = async () => {
  try {
    loadingCall.value = true
    const [callResponse, closingTimeResponse] = await Promise.all([
      getCallById(callId.value),
      getClosingTime(callId.value)
    ])
    callData.value = callResponse
    closingTimeISO.value = closingTimeResponse.closingTime 
  } catch (error) {
    console.error("Error al cargar detalles de la convocatoria:", error)
  } finally {
    loadingCall.value = false
  }
}

const loadProposals = async () => {
  try {
    loadingProposals.value = true
    const list = await getProposalsByCall(callId.value)
    proposals.value = list
  } catch (error) {
    console.error("Error al cargar las propuestas:", error)
  } finally {
    loadingProposals.value = false
  }
}

const calculateFileHash = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const arrayBuffer = e.target.result
      const hashResult = keccak256(arrayBuffer)
      resolve(`0x${hashResult}`.toLowerCase())
    }
    reader.readAsArrayBuffer(file)
  })
}

const processIncomingFiles = async (files) => {
  fileError.value = null
  const maxSize = 10 * 1024 * 1024
  for (let file of files) {
    if (file.size > maxSize) {
      fileError.value = `El archivo "${file.name}" supera el límite de 10MB.`
      continue
    }
    const fileIdx = selectedFilesList.value.length
    selectedFilesList.value.push({ name: file.name, size: file.size, hash: '', hashing: true })
    const hashResult = await calculateFileHash(file)
    selectedFilesList.value[fileIdx].hash = hashResult
    selectedFilesList.value[fileIdx].hashing = false
  }
}

const onFilesSelected = (e) => { if (e.target.files) processIncomingFiles(e.target.files) }
const onFilesDropped = (e) => { if (!submitting.value && e.dataTransfer?.files) processIncomingFiles(e.dataTransfer.files) }
const removeFile = (index) => { selectedFilesList.value.splice(index, 1) }

const resetFormAndOpen = () => {
  if (hasRestrictedRole.value) return
  formProposal.value.title = ''
  formProposal.value.description = ''
  selectedFilesList.value = []
  fileError.value = null
  if (formRef.value) formRef.value.resetValidation()
  dialogOpen.value = true
}

const submitProposal = async () => {
  if (!formRef.value || hasRestrictedRole.value) return
  const { valid } = await formRef.value.validate()
  if (!valid) return
  if (selectedFilesList.value.length === 0) {
    fileError.value = 'Debes incluir al menos un archivo comprobatorio.'
    return
  }
  try {
    submitting.value = true
    const payload = {
      callId: callId.value,
      title: formProposal.value.title,
      description: formProposal.value.description,
      files: selectedFilesList.value.map(file => file.hash)
    }
    await apiRegisterProposal(payload)
    dialogOpen.value = false
    await loadProposals()
  } catch (error) {
    fileError.value = `Error en el servidor: ${error.response?.data?.message || 'Error interno.'}`
  } finally {
    submitting.value = false
  }
}

const downloadReceipt = async (proposalId) => {
  try {
    const receiptData = await getProposalReceipt(proposalId)
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(receiptData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `recibo_inicial_${proposalId.substring(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (error) {
    alert("Error al descargar el recibo de la propuesta.")
  }
}

const triggerReceiptSelection = (proposalId) => {
  if (!hasRestrictedRole.value) {
    const inputEl = document.getElementById(`receipt-input-${proposalId}`)
    if (inputEl) inputEl.click()
  }
}

const handleReceiptUpload = (event, proposalId) => {
  const file = event.target.files[0]
  if (!file) return
  verifyingId.value = proposalId
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const receiptJson = JSON.parse(e.target.result)
      const result = await verifyProposalReceipt(receiptJson)
      verificationDialog.value = {
        open: true,
        success: result.valid,
        message: result.valid ? (result.message || 'El recibo es válido.') : (result.reason || 'Falló la validación.')
      }
    } catch (err) {
      verificationDialog.value = { open: true, success: false, message: 'JSON inválido o corrupto.' }
    } finally {
      verifyingId.value = null
      event.target.value = '' 
    }
  }
  reader.readAsText(file)
}

const openPostClosingModal = (proposal) => {
  if (hasRestrictedRole.value) return
  selectedProposal.value = proposal
  postClosingReceiptFile.value = null
  postClosingFilesList.value = []
  postClosingError.value = null
  postClosingDialogOpen.value = true
}

const onReceiptFileChanged = (e) => {
  const files = e.target.files || e.dataTransfer?.files
  if (files && files.length > 0) postClosingReceiptFile.value = files[0]
}
const onPostClosingFilesChanged = (e) => {
  const files = e.target.files || e.dataTransfer?.files
  if (files) postClosingFilesList.value = Array.from(files)
}

const submitPostClosingData = async () => {
  if (!postClosingReceiptFile.value || postClosingFilesList.value.length === 0 || hasRestrictedRole.value) return
  const reader = new FileReader()
  submittingPostClosing.value = true
  reader.onload = async (e) => {
    try {
      const formData = new FormData()
      formData.append('receipt_data', e.target.result)
      postClosingFilesList.value.forEach(file => formData.append('uploaded_files', file))
      await submitPostClosing(formData)
      postClosingDialogOpen.value = false
      verificationDialog.value = { open: true, success: true, message: 'Entrega post-cierre procesada.' }
      await loadProposals()
    } catch (error) {
      postClosingError.value = `Fallo: ${error.response?.data?.message || 'Error crítico.'}`
    } finally {
      submittingPostClosing.value = false
    }
  }
  reader.readAsText(postClosingReceiptFile.value)
}

onMounted(() => {
  if (callId.value) { loadCallDetails(); loadProposals(); }
  clockInterval = setInterval(() => { currentTime.value = new Date() }, 1000)
})
onBeforeUnmount(() => { if (clockInterval) clearInterval(clockInterval) })
</script>

<style scoped>
.bg-container { min-height: 100vh; overflow: hidden; }
.blur-background { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-size: cover; background-position: center; filter: blur(10px) brightness(0.85); transform: scale(1.05); z-index: 0; }
.z-index-1 { z-index: 1; }
.main-panel { background-color: rgba(248, 250, 252, 0.92) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.6); height: 85vh; display: flex; flex-direction: column; }
.bg-slate-light { background-color: #ffffff !important; border: 1px solid #e2e8f0; }
.bg-slate-light-flat { background-color: #f8fafc !important; }
.border-light { border: 1px solid #e2e8f0 !important; }
.italic-description { font-style: italic; word-wrap: break-word; white-space: normal; }
.text-slate-dark { color: #0f172a !important; }
.text-slate-medium { color: #475569 !important; }
.text-mono { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
.proposals-scroll-containerpe { overflow-y: auto; flex-grow: 1; }
.proposal-row { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; transition: all 0.2s ease-in-out; }
.proposal-row :deep(.v-expansion-panel-title--active) { background-color: #f1f5f9 !important; }
.text-xxs { font-size: 0.7rem; }
.max-w-70 { max-width: 70%; }
</style>