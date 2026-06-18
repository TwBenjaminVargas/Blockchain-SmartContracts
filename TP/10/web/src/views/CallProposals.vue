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
                <v-chip color="error" size="small" variant="flat" class="font-weight-bold rounded-lg">
                    Cierre: {{ formatTimestamp(closingTimeISO) }}
                </v-chip>
              </div>
            </v-card>

            <div class="d-flex justify-space-between align-center mb-4">
              <h4 class="text-subtitle-1 font-weight-bold text-slate-dark">
                Listado de Postulaciones ({{ proposals.length }})
              </h4>
              <v-btn
                color="indigo-darken-1"
                variant="flat"
                class="rounded-lg font-weight-bold text-white px-4 shadow-sm"
                @click="dialogOpen = true"
              >
                Añadir Propuesta
              </v-btn>
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
                        <v-icon icon="mdi-file-document-outline" color="indigo-darken-1" class="me-2"></v-icon>
                        <span>{{ proposal.title }}</span>
                      </div>
                      <v-chip
                        :color="proposal.filesDelivered ? 'success' : 'warning'"
                        size="small"
                        variant="flat"
                        class="font-weight-bold rounded-lg"
                      >
                        {{ proposal.filesDelivered ? 'Archivos Recibidos' : 'Registrada' }}
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
                      <v-btn
                        color="secondary"
                        variant="outlined"
                        prepend-icon="mdi-receipt-text-outline"
                        class="rounded-lg font-weight-bold border-light text-slate-dark"
                        @click="downloadReceipt(proposal.proposalId)"
                      >
                        Descargar Recibo
                      </v-btn>
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
            <v-icon icon="mdi-file-plus-outline" color="indigo-darken-1" class="me-2"></v-icon>
            Nueva Propuesta
          </div>
          <v-btn variant="text" icon="mdi-close" color="slate-medium" @click="dialogOpen = false"></v-btn>
        </v-card-title>
        
        <v-divider class="my-2"></v-divider>

        <v-card-text class="pa-2">
          <v-form>
            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Título de la propuesta *</div>
            <v-text-field
              placeholder="Ej: Desarrollo de Infraestructura Descentralizada"
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-2"
              density="comfortable"
            ></v-text-field>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Descripción Corta *</div>
            <v-textarea
              placeholder="Detalla los alcances técnicos resumidos de tu postulación..."
              variant="outlined"
              color="indigo-darken-1"
              class="rounded-lg mb-4"
              rows="3"
              auto-grow
              density="comfortable"
            ></v-textarea>

            <div class="text-subtitle-2 font-weight-bold text-slate-dark mb-2">Archivos Comprobatorios *</div>
            <div class="drag-drop-zone d-flex flex-column align-center justify-center pa-6 rounded-xl text-center">
              <v-icon icon="mdi-cloud-upload-outline" color="indigo-darken-1" size="48" class="mb-2"></v-icon>
              <div class="text-body-2 font-weight-bold text-slate-dark mb-1">
                Arrastra tus archivos aquí o haz clic para buscar
              </div>
              <div class="text-caption text-slate-medium mb-3">
                Formatos permitidos: PDF, ZIP, DOCX (Máx. 10MB c/u)
              </div>
              <v-btn 
                color="indigo-darken-1" 
                variant="tonal" 
                size="small" 
                class="rounded-lg font-weight-bold"
              >
                Seleccionar archivos
              </v-btn>
            </div>
          </v-form>
        </v-card-text>

        <v-card-actions class="justify-end pa-2 border-top mt-4">
          <v-btn 
            variant="text" 
            color="slate-medium" 
            class="rounded-lg font-weight-bold px-4" 
            @click="dialogOpen = false"
          >
            Cancelar
          </v-btn>
          <v-btn 
            color="indigo-darken-1" 
            variant="flat" 
            class="rounded-lg font-weight-bold px-6 text-white shadow-sm"
          >
            Enviar Propuesta
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
// Agregamos la importación de getClosingTime desde tu capa de servicios
import { getCallById, getProposalsByCall, getProposalReceipt, getClosingTime } from '../services/api'
import { ASSETS } from '../config/constants'

const route = useRoute()
const callId = ref(route.params.callId)
const exit_svg = ASSETS.exitIcon

// Estética
const BACKGROUND_IMAGE = ASSETS.callsProposalsBg

// Estados de carga e información reactiva
const dialogOpen = ref(false)
const loadingCall = ref(true)
const loadingProposals = ref(true)
const callData = ref(null)
const proposals = ref([])
const closingTimeISO = ref(null) // Nuevo estado reactivo para almacenar la fecha ISO del endpoint

// Función auxiliar robustecida para formatear tanto Unix Timestamps (números) como Strings ISO 8601
const formatTimestamp = (value) => {
  if (!value) return 'Sin fecha'
  
  // Si viene en formato String ISO (como el que devuelve /closing-time/{call_id}), instanciamos directamente la fecha
  // Si viene como un timestamp numérico de Unix, multiplicamos por 1000
  const date = typeof value === 'string' ? new Date(value) : new Date(value * 1000)
  
  // Verificamos si la fecha resultante es válida antes de parsear
  if (isNaN(date.getTime())) return 'Fecha inválida'

  return date.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Carga los datos de la Convocatoria desde la API y consulta su tiempo de cierre
const loadCallDetails = async () => {
  try {
    loadingCall.value = true
    
    // Ejecutamos las dos llamadas de forma concurrente para optimizar tiempos de respuesta
    const [callResponse, closingTimeResponse] = await Promise.all([
      getCallById(callId.value),
      getClosingTime(callId.value)
    ])
    
    callData.value = callResponse
    // Guardamos la propiedad 'closingTime' devuelta dentro del JSON por el backend de FastAPI
    closingTimeISO.value = closingTimeResponse.closingTime 
  } catch (error) {
    console.error("Error al cargar detalles de la convocatoria o fecha de cierre:", error)
  } finally {
    loadingCall.value = false
  }
}

// Carga las propuestas vinculadas desde la API
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

// Descarga el recibo de la propuesta en formato JSON para el oferente
const downloadReceipt = async (proposalId) => {
  try {
    const receiptData = await getProposalReceipt(proposalId)
    
    // Convertimos el JSON recibido en un archivo descargable al vuelo
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(receiptData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `recibo_propuesta_${proposalId.substring(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (error) {
    alert("Error al descargar el recibo de la propuesta.")
  }
}

// Ejecución al montar el componente
onMounted(() => {
  if (callId.value) {
    loadCallDetails()
    loadProposals()
  }
})
</script>

<style scoped>
.bg-container {
  min-height: 100vh;
  overflow: hidden;
}

.blur-background {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-size: cover;
  background-position: center;
  filter: blur(10px) brightness(0.85);
  transform: scale(1.05);
  z-index: 0;
}

.z-index-1 {
  z-index: 1;
}

.main-panel {
  background-color: rgba(248, 250, 252, 0.92) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  height: 85vh;
  display: flex;
  flex-direction: column;
}

.bg-slate-light {
  background-color: #ffffff !important;
  border: 1px solid #e2e8f0;
}

.bg-slate-light-flat {
  background-color: #f8fafc !important;
}

.border-light {
  border: 1px solid #e2e8f0 !important;
}

.italic-description {
  font-style: italic;
  word-wrap: break-word;
  white-space: normal;
}

.text-slate-dark {
  color: #0f172a !important;
}

.text-slate-medium {
  color: #475569 !important;
}

.text-mono {
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
}

.proposals-scroll-containerpe {
  overflow-y: auto;
  flex-grow: 1;
}

.proposal-row {
  background-color: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  transition: all 0.2s ease-in-out;
}

.proposal-row :deep(.v-expansion-panel-title--active) {
  background-color: #f1f5f9 !important;
}

.drag-drop-zone {
  border: 2px dashed #cbd5e1;
  background-color: #f8fafc;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.drag-drop-zone:hover {
  border-color: #4f46e5;
  background-color: #f0f2ff;
}

.border-top {
  border-top: 1px solid #e2e8f0;
}

.gap-2 {
  gap: 8px;
}
</style>