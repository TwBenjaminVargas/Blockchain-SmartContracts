<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div class="d-flex justify-center mb-6">
            <v-btn-toggle
              v-model="currentTab"
              mandatory
              color="indigo-darken-1"
              variant="text"
              class="custom-toggle"
            >
              <v-btn value="creators" class="font-weight-bold">Creadores</v-btn>
              <v-btn value="calls" class="font-weight-bold">Llamados</v-btn>
            </v-btn-toggle>
          </div>

          <h2 class="text-h4 font-weight-bold text-center text-slate-dark mb-4">
            {{ panelTitle }}
          </h2>

          <v-card variant="flat" class="bg-slate-light pa-4 rounded-lg mb-4 search-box">
            <v-row dense align="center">
              <v-col cols="12" :sm="currentTab === 'calls' ? '6' : '12'" :md="currentTab === 'calls' ? '3' : '12'">
                <v-text-field
                  v-model="searchQuery"
                  clearable
                  density="compact"
                  variant="outlined"
                  bg-color="white"
                  color="indigo-darken-1"
                  hide-details
                  prepend-inner-icon="mdi-magnify"
                  :label="currentTab === 'calls' ? 'Buscar por título o ID...' : 'Buscar por nombre o dirección (0x...)'"
                ></v-text-field>
              </v-col>

              <template v-if="currentTab === 'calls'">
                <v-col cols="12" sm="6" md="3">
                  <v-text-field
                    v-model="searchCreator"
                    clearable
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    prepend-inner-icon="mdi-account-search-outline"
                    label="Dirección del creador (0x...)"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-select
                    v-model="filterState"
                    :items="stateOptions"
                    label="Filtrar por Estado"
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    clearable
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-select
                    v-model="filterTimeline"
                    :items="timelineOptions"
                    label="Fecha de Cierre"
                    density="compact"
                    variant="outlined"
                    bg-color="white"
                    color="indigo-darken-1"
                    hide-details
                    clearable
                  ></v-select>
                </v-col>
              </template>
            </v-row>
          </v-card>

          <div v-if="currentTab === 'creators'" class="scrollable-containerpe">
            <div 
              v-if="filteredCreators.registered.length === 0 && filteredCreators.external.length === 0" 
              class="text-center py-10 text-grey-darken-1"
            >
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron creadores que coincidan con la búsqueda</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel
                v-for="(creator, index) in filteredCreators.registered"
                :key="creator.address"
                class="creator-row mb-3 rounded-lg overflow-hidden"
                elevation="1"
              >
                <v-expansion-panel-title class="py-4">
                  <v-avatar :color="getRandomColor(index)" size="48" class="me-4 shadow-sm text-white font-weight-bold">
                    {{ creator.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-slate-dark">{{ creator.name }}</div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ creator.address }}</div>
                  </div>
                </v-expansion-panel-title>

                <v-expansion-panel-text class="text-left pt-2 text-slate-medium">
                  <div class="mb-2"><strong class="text-slate-dark">Descripción:</strong> {{ creator.description || 'Sin descripcion provista' }}</div>
                  <div><strong class="text-slate-dark">Nonce: </strong> <span class="text-mono">{{ creator.nonce }}</span></div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel
                v-for="address in filteredCreators.external"
                :key="address"
                class="creator-row external-row mb-3 rounded-lg overflow-hidden"
                elevation="1"
              >
                <v-expansion-panel-title class="py-4">
                  <v-avatar color="grey-lighten-2" size="48" class="me-4 border-dashed text-grey-darken-2">
                    <v-icon icon="mdi-help-outline" size="24"></v-icon>
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">Creador Externo</div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ address }}</div>
                  </div>
                </v-expansion-panel-title>

                <v-expansion-panel-text class="text-left pt-2 text-grey-darken-2 italic-text">
                  Este creador se ha registrado por otros medios y no se posee información al respecto
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div v-else class="scrollable-containerpe">
            <div v-if="loadingCalls" class="d-flex flex-column align-center justify-center py-12">
              <v-progress-circular indeterminate color="indigo-darken-1" size="50" width="4" class="mb-4"></v-progress-circular>
              <p class="text-body-1 text-grey-darken-1 font-weight-medium">Sincronizando catálogo de llamados globales...</p>
            </div>

            <div v-else-if="searchedGlobalCalls.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron llamados que coincidan con los filtros aplicados</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel 
                v-for="call in searchedGlobalCalls" 
                :key="call.callId" 
                :class="['creator-row mb-3 rounded-lg overflow-hidden', !call.isInternal ? 'external-row' : '']" 
                elevation="1"
              >
                <v-expansion-panel-title class="py-4">
                  <v-row no-gutters class="align-center w-100 min-w-0">
                    <v-col cols="12" md="7" class="d-flex flex-column text-left min-w-0 pr-4">
                      <div class="d-flex align-center flex-wrap gap-2 mb-2">
                        <!-- MODIFICADO: Reemplazado Call ID recortado por el Dominio ENS -->
                        <span class="text-mono text-body-2 font-weight-bold text-indigo-darken-1 bg-indigo-lighten-5 px-2 py-0.5 rounded d-inline-flex align-center">
                          <v-icon icon="mdi-dns" size="14" class="me-1"></v-icon>
                          {{ call.domain || 'sin-dominio.llamados.eth' }}
                        </span>
                      
                        <v-chip v-if="call.isInternal" size="small" color="success" variant="flat" class="font-weight-bold text-caption">
                          Sincronizado
                        </v-chip>
                        <v-chip v-else size="small" color="amber-darken-2" variant="flat" class="font-weight-bold text-caption">
                          Blockchain Pura
                        </v-chip>

                        <v-chip v-if="call.isInternal && call.state" size="small" color="indigo-lighten-1" variant="outlined" class="font-weight-bold text-caption">
                          {{ call.state }}
                        </v-chip>
                      </div>

                      <div class="text-subtitle-1 font-weight-bold text-slate-dark text-truncate w-100">
                        {{ call.title || 'Convocatoria Externa (Sin metadatos)' }}
                      </div>
                    </v-col>

                    <v-col cols="12" md="5" class="text-md-right mt-2 mt-md-0 text-body-2">
                      <template v-if="isCallExpired(call.closingTime)">
                        <span class="text-error font-weight-bold">
                          <v-icon icon="mdi-clock-alert-outline" size="16" class="me-1 text-error"></v-icon>
                          Cerró el: {{ formatUnixTimestamp(call.closingTime) }}
                        </span>
                      </template>
                      <template v-else>
                        <span class="text-success font-weight-medium">
                          <v-icon icon="mdi-clock-outline" size="16" class="me-1 text-success"></v-icon>
                          Cierra el: <strong class="text-slate-dark">{{ formatUnixTimestamp(call.closingTime) }}</strong>
                        </span>
                      </template>
                    </v-col>
                  </v-row>
                </v-expansion-panel-title>

                <v-expansion-panel-text class="text-left pt-2 text-slate-medium">
                  <h4 class="text-subtitle-1 font-weight-bold text-slate-dark mb-1">
                    {{ call.title || 'Convocatoria Externa' }}
                  </h4>
                  <p class="text-body-2 text-slate-medium mb-3">
                    {{ call.description || 'Este llamado reside únicamente en los nodos de la Blockchain y no cuenta con metadatos extendidos guardados en la base de datos de la API.' }}
                  </p>
                  
                  <v-divider class="mb-3"></v-divider>

                  <!-- MODIFICADO: Estructura técnica ordenada por cajas con separación por items y botones de copia -->
                  <div class="technical-details d-flex flex-column gap-3 text-body-2 text-grey-darken-3 mb-4">
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-file-sign" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Address:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.contractAddress || call.address || 'No desplegado / 0x00...' }}</span>
                      </div>
                      <v-btn 
                        v-if="call.contractAddress || call.address"
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Address"
                        @click="copyToClipboard(call.contractAddress || call.address, 'Contract Address')"
                      ></v-btn>
                    </div>
                  
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-account-circle" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Creador (Wallet):</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.creator }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Creador"
                        @click="copyToClipboard(call.creator, 'Wallet del Creador')"
                      ></v-btn>
                    </div>
                  
                    <div class="d-flex align-center justify-space-between bg-white pa-2 rounded-lg border">
                      <div class="text-truncate pr-2">
                        <v-icon icon="mdi-identifier" size="16" class="me-2 text-indigo-darken-1"></v-icon>
                        <strong>Call ID:</strong>  
                        <span class="text-mono ms-2 text-caption text-grey-darken-1 select-all">{{ call.callId }}</span>
                      </div>
                      <v-btn 
                        icon="mdi-content-copy" 
                        variant="text" 
                        size="x-small" 
                        color="indigo-darken-1"
                        title="Copiar Call ID"
                        @click="copyToClipboard(call.callId, 'Call ID')"
                      ></v-btn>
                    </div>

                    <div v-if="call.state === 'CREATED'" class="d-flex justify-end mt-2">
                      <v-btn
                        color="indigo-darken-1"
                        variant="elevated"
                        class="rounded-lg font-weight-bold"
                        @click="$router.push({ name: 'call-proposals', params: { callId: call.callId } })"
                      >
                        Ver propuestas
                      </v-btn>
                    </div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

        </v-card>
      </v-col>
    </v-row>
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      elevation="4"
      location="top right"
      :timeout="4000"
      class="mt-4"
    >
      <div class="d-flex align-center">
        <v-icon 
          :icon="snackbar.color === 'success' ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline'" 
          class="me-3" 
          size="22"
        ></v-icon>
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
import { ASSETS } from '../config/constants'
import { getCreators, getGlobalCalls } from '../services/api'
import {resolveDomain} from '../services/ens'

const backgroundImage = ASSETS.genericBg
const currentTab = ref('creators')
const loadingCalls = ref(false)
const question_svg = ASSETS.questionIcon

// Variables Reactivas de Búsqueda y Filtrado
const searchQuery = ref('')
const searchCreator = ref('')
const filterState = ref(null)
const filterTimeline = ref(null)

const registeredCreators = ref([])
const externalCreators = ref([])
const internalGlobalCalls = ref([])
const externalGlobalCalls = ref([])

const stateOptions = [
  { title: 'Todos los estados', value: null },
  { title: 'Sincronizados (Base Local)', value: 'internal' },
  { title: 'Blockchain Pura', value: 'external' },
  { title: 'Estado: CREATED', value: 'CREATED' },
  { title: 'Estado: PENDING', value: 'PENDING' }
]

const timelineOptions = [
  { title: 'Cualquier fecha', value: null },
  { title: 'Vigentes / Abiertos', value: 'open' },
  { title: 'Expirados / Cerrados', value: 'expired' }
]

const avatarColors = [
  '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', 
  '#ec4899', '#8b5cf6', '#3b82f6', '#f43f5e'
]

const panelTitle = computed(() => {
  return currentTab.value === 'creators' ? 'Listado de Creadores' : 'Catálogo Global de Convocatorias'
})

const domainLinkedStatus = ref({})
const snackbar = ref({ show: false, message: '', color: 'error' })

function showSnackbar(message, color = 'error') {
  snackbar.value = { show: true, message, color }
}



// Vigilante para resetear filtros al permutar de pestaña
watch(currentTab, () => {
  searchQuery.value = ''
  searchCreator.value = ''
  filterState.value = null
  filterTimeline.value = null
  loadAllData()
})

function getRandomColor(index) {
  return avatarColors[index % avatarColors.length]
}

function isCallExpired(closingTime) {
  if (!closingTime) return false
  const currentUnixTime = Math.floor(Date.now() / 1000)
  return Number(closingTime) < currentUnixTime
}

function formatUnixTimestamp(timestamp) {
  if (!timestamp) return 'No definido'
  const date = new Date(Number(timestamp) * 1000)
  return date.toLocaleString(navigator.language, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// FILTRADO DINÁMICO: PESTAÑA CREADORES
const filteredCreators = computed(() => {
  const query = searchQuery.value?.toLowerCase().trim() || ''
  
  const regFiltered = registeredCreators.value.filter(c => 
    c.name.toLowerCase().includes(query) || c.address.toLowerCase().includes(query)
  )
  const extFiltered = externalCreators.value.filter(addr => 
    addr.toLowerCase().includes(query)
  )

  return { registered: regFiltered, external: extFiltered }
})

// FILTRADO DINÁMICO MULTI-CRITERIO: PESTAÑA LLAMADOS
const searchedGlobalCalls = computed(() => {
  const internals = internalGlobalCalls.value.map(c => ({ ...c, isInternal: true }))
  const externals = externalGlobalCalls.value.map(c => ({ ...c, isInternal: false }))
  let unified = [...internals, ...externals]

  // Filtrar por barra de texto (Título, Dirección del contrato, CallID)
  const query = searchQuery.value?.toLowerCase().trim() || ''
  if (query) {
    unified = unified.filter(call => {
      const titleMatch = call.title?.toLowerCase().includes(query) || false
      const idMatch = call.callId?.toLowerCase().includes(query) || false
      const addressMatch = (call.contractAddress || call.address)?.toLowerCase().includes(query) || false
      return titleMatch || idMatch || addressMatch
    })
  }

  // Filtrar por Dirección específica del Creador (Wallet)
  const creatorQuery = searchCreator.value?.toLowerCase().trim() || ''
  if (creatorQuery) {
    unified = unified.filter(call => 
      call.creator?.toLowerCase().includes(creatorQuery) || false
    )
  }

  // 3. Filtrar por Estado (Sincronizado, Blockchain Pura o estados de ciclo de vida local)
  if (filterState.value) {
    if (filterState.value === 'internal') {
      unified = unified.filter(c => c.isInternal)
    } else if (filterState.value === 'external') {
      unified = unified.filter(c => !c.isInternal)
    } else {
      unified = unified.filter(c => c.state === filterState.value)
    }
  }

  // 4. Filtrar por línea de tiempo (Vigentes vs Expirados)
  if (filterTimeline.value) {
    const isExpiredTarget = filterTimeline.value === 'expired'
    unified = unified.filter(c => isCallExpired(c.closingTime) === isExpiredTarget)
  }

  return unified
})

async function loadAllData() {
  try {
    if (currentTab.value === 'calls') {
      loadingCalls.value = true
      const callsCatalog = await getGlobalCalls()
      if (callsCatalog) {
        internalGlobalCalls.value = callsCatalog.internal || []
        externalGlobalCalls.value = callsCatalog.external || []
      }
      loadingCalls.value = false
      return
    }

    const creatorsData = await getCreators()
    registeredCreators.value = creatorsData.registered_creators || []
    externalCreators.value = creatorsData.external_creators || []
  } catch (error) {
    console.error("Error al cargar los datos del panel público:", error)
    loadingCalls.value = false
  }
}

async function copyToClipboard(text, label) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    showSnackbar(`¡${label} copiado al portapapeles!`, 'success')
  } catch (err) {
    console.error('Error al copiar:', err)
    showSnackbar('No se pudo copiar el elemento.')
  }
}

onMounted(() => {
  loadAllData()
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

.scrollable-containerpe {
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 8px;
}

.bg-slate-light {
  background-color: #f1f5f9 !important;
  border: 1px solid #e2e8f0;
}

.search-box {
  flex-shrink: 0;
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

.creator-row {
  background-color: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  transition: all 0.2s ease-in-out;
}

.creator-row :deep(.v-expansion-panel-title) {
  background-color: #ffffff !important;
}

.creator-row :deep(.v-expansion-panel-title--active) {
  background-color: #f1f5f9 !important;
}

.external-row {
  border: 1px dashed #cbd5e1 !important;
}

.border-dashed {
  border: 2px dashed #94a3b8 !important;
}

.italic-text {
  font-style: italic;
}

.select-all {
  user-select: all;
}

.scrollable-containerpe::-webkit-scrollbar {
  width: 6px;
}
.scrollable-containerpe::-webkit-scrollbar-track {
  background: transparent;
}
.scrollable-containerpe::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.scrollable-containerpe::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>