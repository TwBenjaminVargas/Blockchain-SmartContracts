<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="10" md="8" lg="6" class="pa-4">
        
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

          <h2 class="text-h4 font-weight-bold text-center text-slate-dark mb-6">
            Listado de creadores
          </h2>

          <div v-if="currentTab === 'creators'" class="scrollable-containerpe">
            
            <div 
              v-if="registeredCreators.length === 0 && externalCreators.length === 0" 
              class="text-center py-10 text-grey-darken-1"
            >
              <v-icon icon="mdi-account-off-outline" size="64" class="mb-3 text-grey-lighten-1"></v-icon>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron creadores registrados</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              
              <v-expansion-panel
                v-for="(creator, index) in registeredCreators"
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
                  <div class="mb-2">
                    <strong class="text-slate-dark">Descripción:</strong> 
                    {{ creator.description || 'Sin descripcion provista' }}
                  </div>
                  <div>
                    <strong class="text-slate-dark">Nonce: </strong> 
                    <span class="text-mono">{{ creator.nonce }}</span>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel
                v-for="address in externalCreators"
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

          <div v-else class="text-center py-8 text-grey-darken-1">
            <v-icon icon="mdi-hourglass-empty" size="48" class="mb-2 text-grey-lighten-1"></v-icon>
            <p>Sección de llamados en desarrollo. Próximamente disponible.</p>
          </div>

        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ASSETS } from '../config/constants'
import { getCreators } from '../services/api'

const backgroundImage = ASSETS.genericBg
const currentTab = ref('creators')

const registeredCreators = ref([])
const externalCreators = ref([])

const avatarColors = [
  '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', 
  '#ec4899', '#8b5cf6', '#3b82f6', '#f43f5e'
]

function getRandomColor(index) {
  return avatarColors[index % avatarColors.length]
}

async function fetchCreatorsData() {
  try {
    const data = await getCreators()
    registeredCreators.value = data.registered_creators || []
    externalCreators.value = data.external_creators || []
  } catch (error) {
    console.error("Error al cargar los creadores:", error)
  }
}

onMounted(() => {
  fetchCreatorsData()
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
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.scrollable-containerpe {
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 4px;
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

.custom-title {
  font-family: 'Inter', sans-serif !important;
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