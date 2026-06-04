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

          <h2 class="text-h4 font-weight-bold text-center text-slate-dark mb-6">
            {{ panelTitle }}
          </h2>

          <div v-if="currentTab === 'calls'" class="text-center py-10 text-grey-darken-1 flex-grow-1 d-flex flex-column justify-center">
            <v-img :src="question_svg" max-width="80" class="mx-auto mb-4" opacity="0.6"></v-img>
            <p class="text-subtitle-1 font-weight-medium">Sección de llamados creados en desarrollo.</p>
            <p class="text-caption text-grey-darken-1">Próximamente disponible.</p>
          </div>

        </v-card>
      </v-col>
    </v-row>

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
  updateRegistration 
} from '../services/api'

const walletStore = useWalletStore()

const backgroundImage = ASSETS.creatorBg
const question_svg = ASSETS.questionIcon
const pencilIcon = ASSETS.pencilIcon
const currentTab = ref('calls')

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

const panelTitle = computed(() => {
  if (currentTab.value === 'calls') return 'Gestión de Llamados'
  return ''
})

function showSnackbar(message, color = 'error') {
  snackbar.value = { show: true, message, color }
}

// Sincroniza la información llamando al endpoint usando la cuenta activa de Pinia
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
    if (!factoryAddress) throw new Error('No se pudo mapear la dirección del contrato factory.')

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

    // Se compone el mensaje usando el nonce exacto sincronizado del backend
    const message = {
      operation: "update",
      contract: checksumContractAddress,
      nonce: creatorData.value.nonce,
      name: editModal.value.form.name
    }

    console.log("%c[Perfil] Solicitando firma para actualización...", "color: #4f46e5; font-weight: bold;", message)

    const signature = await signer.signTypedData(domain, types, message)

    const payload = {
      name: editModal.value.form.name,
      description: editModal.value.form.description,
      signature: signature
    }

    // Petición PATCH al backend
    await updateRegistration(walletStore.account, payload)

    showSnackbar("¡Perfil actualizado con éxito!", "success")
    editModal.value.show = false
    
    // Al re-consultar, el backend devolverá el nonce incrementado (nonce + 1) de forma consistente
    await fetchCreatorProfile()

  } catch (error) {
    console.error("Error al actualizar perfil:", error)
    let alertMsg = 'Ocurrió un problema al actualizar tu perfil.'
    if (error.response && error.response.data && error.response.data.message) {
      alertMsg = `Error: ${error.response.data.message}`
    } else if (error.code === 'ACTION_REJECTED') {
      alertMsg = 'Firma denegada en MetaMask.'
    } else if (error.message) {
      alertMsg = error.message
    }
    showSnackbar(alertMsg)
  } finally {
    editModal.value.loading = false
  }
}

onMounted(() => {
  fetchCreatorProfile()
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

.gap-2 {
  gap: 8px;
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
</style>