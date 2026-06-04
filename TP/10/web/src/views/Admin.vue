<template>
  <v-container class="fill-height ma-0 pa-0 bg-container position-relative" fluid>
    <div class="blur-background" :style="{ backgroundImage: `url(${backgroundImage})` }"></div>

    <v-row class="fill-height ma-0 align-center justify-center position-relative z-index-1" no-gutters>
      <v-col cols="12" sm="11" md="10" lg="8" class="pa-4">
        
        <v-card class="main-panel pa-6 rounded-xl mx-auto" elevation="4">
          
          <div class="d-flex justify-center mb-6 overflow-x-auto">
            <v-btn-toggle
              v-model="currentTab"
              mandatory
              color="indigo-darken-1"
              variant="text"
              class="custom-toggle"
            >
              <v-btn value="creators" class="font-weight-bold">Creadores</v-btn>
              <v-btn value="users" class="font-weight-bold">Usuarios</v-btn>
              <v-btn value="requests" class="font-weight-bold">
                Solicitudes
                <v-badge v-if="totalRequests > 0" :content="totalRequests" color="error" inline class="ms-1"></v-badge>
              </v-btn>
              <v-btn value="calls" class="font-weight-bold">Llamados</v-btn>
            </v-btn-toggle>
          </div>

          <h2 class="text-h4 font-weight-bold text-center text-slate-dark mb-6">
            {{ panelTitle }}
          </h2>

          <div v-if="currentTab === 'creators'" class="scrollable-containerpe">
            <div v-if="registeredCreators.length === 0 && externalCreators.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No se encontraron creadores registrados</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel v-for="(creator, index) in registeredCreators" :key="creator.address" class="creator-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar :color="getRandomColor(index)" size="48" class="me-4 shadow-sm text-white font-weight-bold">
                    {{ creator.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-slate-dark">
                      {{ creator.name }}
                      <span v-if="isCurrentUser(creator.address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                    </div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ creator.address }}</div>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-slate-medium">
                  <div class="mb-2"><strong class="text-slate-dark">Descripción:</strong> {{ creator.description || 'Sin descripcion provista' }}</div>
                  <div class="mb-4"><strong class="text-slate-dark">Nonce: </strong> <span class="text-mono">{{ creator.nonce }}</span></div>
                  <div class="text-right">
                    <v-btn 
                      v-if="!isCurrentUser(creator.address)"
                      color="error" 
                      variant="tonal" 
                      size="small" 
                      class="font-weight-bold" 
                      :loading="isActionLoading === creator.address" 
                      @click="handleAction('unauthorize', creator.address)"
                    > Desautorizar
                    </v-btn>
                    <v-chip v-else color="indigo-lighten-4" text-color="indigo-darken-4" size="small" class="font-weight-bold">Administrador Activo</v-chip>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel v-for="address in externalCreators" :key="address" class="creator-row external-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar color="grey-lighten-2" size="48" class="me-4 border-dashed text-grey-darken-2">
                    <v-icon icon="mdi-help-outline" size="24"></v-icon>
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">
                      Creador Externo
                      <span v-if="isCurrentUser(address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                    </div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ address }}</div>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-grey-darken-2">
                  <p class="italic-text mb-4">Este creador se ha registrado por otros medios y no se posee información al respecto</p>
                  <div class="text-right">
                    <v-btn 
                      v-if="!isCurrentUser(address)"
                      color="error" 
                      variant="tonal" 
                      size="small" 
                      class="font-weight-bold" 
                      :loading="isActionLoading === address" 
                      @click="handleAction('unauthorize', address)"
                    > Desautorizar
                    </v-btn>
                    <v-chip v-else color="indigo-lighten-4" text-color="indigo-darken-4" size="small" class="font-weight-bold">Administrador Activo</v-chip>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div v-else-if="currentTab === 'users'" class="scrollable-containerpe">
            <div v-if="filteredUsers.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No hay usuarios activos o archivados para mostrar.</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel
                v-for="(user, index) in filteredUsers"
                :key="user.address"
                :class="['creator-row mb-3 rounded-lg overflow-hidden', user.state === 'archived' ? 'archived-row' : '']"
                elevation="1"
              >
                <v-expansion-panel-title class="py-4">
                  <v-avatar :color="user.state === 'archived' ? 'grey' : getRandomColor(index)" size="48" class="me-4 text-white font-weight-bold">
                    {{ user.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                  <div class="text-left w-100 d-flex justify-space-between align-center pe-4">
                    <div>
                      <div class="text-subtitle-1 font-weight-bold text-slate-dark">
                        {{ user.name }}
                        <span v-if="isCurrentUser(user.address)" class="text-caption text-indigo font-weight-bold ms-1">(Tú)</span>
                      </div>
                      <div class="text-caption text-mono text-grey-darken-1">{{ user.address }}</div>
                    </div>
                    <v-chip :color="user.state === 'archived' ? 'grey' : 'success'" size="small" variant="flat" class="font-weight-bold text-uppercase">
                      {{ user.state }}
                    </v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-slate-medium">
                  <div class="mb-2"><strong class="text-slate-dark">Descripción:</strong> {{ user.description || 'Sin descripcion provista' }}</div>
                  <div class="mb-4"><strong class="text-slate-dark">Nonce: </strong> <span class="text-mono">{{ user.nonce }}</span></div>
                  
                  <div class="text-right">
                    <v-chip v-if="isCurrentUser(user.address)" color="indigo-lighten-4" text-color="indigo-darken-4" size="small" class="font-weight-bold">
                      Administrador Activo (Tú)
                    </v-chip>

                    <v-chip v-else-if="user.state === 'archived'" color="grey-lighten-2" text-color="grey-darken-1" size="small" class="font-weight-bold">
                      Acciones deshabilitadas (Archivado)
                    </v-chip>

                    <v-btn 
                      v-else
                      color="error" 
                      variant="tonal" 
                      size="small" 
                      class="font-weight-bold" 
                      :loading="isActionLoading === user.address" 
                      @click="handleAction('unauthorize', user.address)"
                    > 
                      Desautorizar
                    </v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div v-else-if="currentTab === 'requests'" class="scrollable-containerpe">
            <div v-if="localRequests.length === 0 && externalRequests.length === 0" class="text-center py-10 text-grey-darken-1">
              <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
              <p class="text-subtitle-1 font-weight-medium">No hay solicitudes de autorización pendientes.</p>
            </div>

            <v-expansion-panels v-else variant="accordion" class="custom-panels">
              <v-expansion-panel v-for="(req, index) in localRequests" :key="req.address" class="creator-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar :color="getRandomColor(index)" size="48" class="me-4 text-white font-weight-bold">
                    {{ req.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-slate-dark">{{ req.name }}</div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ req.address }}</div>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-slate-medium">
                  <div class="mb-4"><strong class="text-slate-dark">Descripción:</strong> {{ req.description || 'Sin descripcion provista' }}</div>
                  <div class="d-flex justify-end gap-2">
                    <v-btn color="error" variant="text" class="font-weight-bold" :disabled="isActionLoading === req.address" @click="handleAction('unauthorize', req.address)">Rechazar</v-btn>
                    <v-btn color="success" variant="flat" class="font-weight-bold" :loading="isActionLoading === req.address" @click="handleAction('authorize', req.address)">Autorizar</v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

               <v-expansion-panel v-for="address in externalRequests" :key="address" class="creator-row external-row mb-3 rounded-lg overflow-hidden" elevation="1">
                <v-expansion-panel-title class="py-4">
                  <v-avatar color="grey-lighten-2" size="48" class="me-4 border-dashed text-grey-darken-2">
                    <v-icon icon="mdi-help-network-outline" size="24"></v-icon>
                  </v-avatar>
                  <div class="text-left">
                    <div class="text-subtitle-1 font-weight-bold text-grey-darken-3">Solicitud Externa</div>
                    <div class="text-caption text-mono text-grey-darken-1">{{ address }}</div>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="text-left pt-2 text-grey-darken-2">
                  <div class="mb-4"><strong class="text-slate-dark">Descripción:</strong> <span class="italic-text">Sin descripción provista</span></div>
                  <div class="d-flex justify-end gap-2">
                    <v-btn color="error" variant="text" class="font-weight-bold" :disabled="isActionLoading === address" @click="handleAction('unauthorize', address)">Rechazar</v-btn>
                    <v-btn color="success" variant="flat" class="font-weight-bold" :loading="isActionLoading === address" @click="handleAction('authorize', address)">Autorizar</v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div v-else class="text-center py-8 text-grey-darken-1">
            <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
            <p>Sección de llamados en desarrollo. Próximamente disponible.</p>
          </div>

        </v-card>
      </v-col>
    </v-row>
    
    </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ethers } from 'ethers'
import { ASSETS } from '../config/constants'
import { useWalletStore } from '../stores/wallet'
import { 
  getCreators, 
  getUsers, 
  getAuthorizationRequests, 
  authorizeUser, 
  unauthorizeUser, 
  getContractAddress, 
  getAdminNonce 
} from '../services/api' 

const walletStore = useWalletStore()

const backgroundImage = ASSETS.adminBg
const currentTab = ref('creators')
const isActionLoading = ref(null)

const question_svg = ASSETS.questionIcon

const snackbar = ref({
  show: false,
  message: ''
})

// Estados
const registeredCreators = ref([])
const externalCreators = ref([])
const allUsers = ref([])
const localRequests = ref([])
const externalRequests = ref([])

const totalRequests = computed(() => localRequests.value.length + externalRequests.value.length)

const panelTitle = computed(() => {
  if (currentTab.value === 'creators') return 'Listado de Creadores'
  if (currentTab.value === 'users') return 'Gestión de Usuarios'
  if (currentTab.value === 'requests') return 'Solicitudes de Autorización'
  return 'Llamados'
})

const filteredUsers = computed(() => {
  return allUsers.value.filter(u => u.state !== 'pending' && u.state !== 'registered')
})

function isCurrentUser(targetAddress) {
  if (!walletStore.account || !targetAddress) return false
  return walletStore.account.toLowerCase() === targetAddress.toLowerCase()
}

const avatarColors = [
  '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', 
  '#ec4899', '#8b5cf6', '#3b82f6', '#f43f5e'
]

function getRandomColor(index) {
  return avatarColors[index % avatarColors.length]
}

async function loadAllData() {
  try {
    const creatorsData = await getCreators()
    registeredCreators.value = creatorsData.registered_creators || []
    externalCreators.value = creatorsData.external_creators || []

    const usersData = await getUsers()
    allUsers.value = usersData.users || []

    const requestsData = await getAuthorizationRequests()
    localRequests.value = requestsData.local_requests || []
    externalRequests.value = requestsData.external_requests || []
  } catch (error) {
    console.error("Error al cargar los datos del panel:", error)
  }
}

async function handleAction(actionType, targetAddress) {
  try {
    if (isCurrentUser(targetAddress) && actionType === 'unauthorize') {
      throw new Error('Operación abortada: No puedes desautorizar tu propia cuenta de administrador.')
    }

    // Validación extra en el script para prevenir firmas en archivados
    const targetUser = allUsers.value.find(u => u.address.toLowerCase() === targetAddress.toLowerCase())
    if (targetUser && targetUser.state === 'archived') {
      throw new Error('Operación abortada: No se pueden realizar acciones sobre usuarios archivados.')
    }

    isActionLoading.value = targetAddress

    if (!window.ethereum) throw new Error('MetaMask no está disponible en este navegador.')

    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const network = await provider.getNetwork()  
    const chainId = parseInt(network.chainId.toString(), 10)

    const factoryAddressResult = await getContractAddress()
    const factoryAddress = typeof factoryAddressResult === 'string' ? factoryAddressResult : factoryAddressResult.address
    
    if (!factoryAddress) throw new Error('No se pudo mapear la dirección del contrato.')

    const checksumContractAddress = ethers.getAddress(factoryAddress.trim())
    const checksumTargetAddress = ethers.getAddress(targetAddress.trim())

    const adminNonce = await getAdminNonce()

    const domain = {
      name: "CFP API",
      version: "1",
      chainId: chainId,
      verifyingContract: checksumContractAddress
    }

    const types = {
      AdminActionRequest: [
        { name: "operation", type: "string" },
        { name: "contract", type: "address" },
        { name: "nonce", type: "uint256" },
        { name: "target", type: "address" }
      ]
    }

    const operationString = actionType === 'authorize' ? 'authorize' : 'unauthorize'

    const message = {
      operation: operationString,
      contract: checksumContractAddress,
      nonce: adminNonce,
      target: checksumTargetAddress
    }

    console.log(`%c[Admin] Firmando orden de ${operationString}...`, "color: #eab308; font-weight: bold;", message)

    const signature = await signer.signTypedData(domain, types, message)
    const payload = { signature }

    if (actionType === 'authorize') {
      await authorizeUser(targetAddress, payload)
    } else {
      await unauthorizeUser(targetAddress, payload)
    }

    await loadAllData()

  } catch (error) {
    console.error(`Error al ejecutar la acción ${actionType} para ${targetAddress}:`, error)
    
    let alertMsg = `Ocurrió un error al procesar la acción para ${targetAddress}.`
    if (error.response && error.response.data && error.response.data.message) {
      alertMsg = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      alertMsg = 'Firma rechazada en MetaMask.'
    } else {
      alertMsg = error.message || alertMsg
    }
    
    snackbar.value = {
      show: true,
      message: alertMsg
    }
  } finally {
    isActionLoading.value = null
  }
}

watch(currentTab, () => {
  loadAllData()
})

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

.archived-row {
  opacity: 0.65;
  filter: grayscale(80%);
}

.border-dashed {
  border: 2px dashed #94a3b8 !important;
}

.italic-text {
  font-style: italic;
}

.gap-2 {
  gap: 8px;
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