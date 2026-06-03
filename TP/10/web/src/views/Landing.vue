<template>
  <v-container class="fill-height ma-0 pa-0 bg-white" fluid>
    <v-row class="fill-height ma-0" no-gutters>
      
      <v-col cols="12" md="6" class="d-flex align-center justify-center bg-landing-light pa-8">
        <div class="landing-content-wrapper">
          
          <div class="title-container mb-6">
            <h1 class="text-h3 font-weight-bold text-slate-dark mb-4 custom-title">
              CFP Client
            </h1>
            <p class="text-body-1 subtitle-text">
                Plataforma de gestion para convocatorias de propuestas
            </p>
          </div>

          <v-alert 
            v-if="walletStore.error" 
            type="error" 
            variant="tonal" 
            class="mb-6 rounded-lg text-left" 
            closable
          >
            {{ walletStore.error }}
          </v-alert>

          <div class="buttons-container">
            
            <v-btn
              :loading="walletStore.isLoading"
              block
              height="56"
              color="#1e40af"
              variant="flat"
              class="mb-4 font-weight-bold rounded-lg text-white text-button"
              @click="handleMetaMaskConnection"
            >
              <template #prepend>
                <img src="/metamask-icon.svg" alt="MetaMask" width="26" height="26" class="me-2" />
              </template>
              CONECTAR METAMASK
            </v-btn>

            <v-btn
              block
              height="56"
              variant="outlined"
              color="#334155"
              class="font-weight-bold rounded-lg text-button custom-guest-btn"
              @click="handleGuestLogin"
            >
              <template #prepend>
                <v-icon icon="md:sharp-person" size="22" class="me-2"></v-icon>
              </template>
              ENTRAR A VISTA PÚBLICA
            </v-btn>

          </div>
        </div>
      </v-col>

      <v-col cols="12" md="6" class="d-none d-md-flex fill-height bg-landing-art position-relative">
        <img :src="backgroundImageRight" alt="Background Art" class="landing-img-fluid" />
        <div class="art-overlay"></div>
      </v-col>

    </v-row>
  </v-container>
</template>

<script setup>
import { useWalletStore } from '../stores/wallet'
import { useRouter } from 'vue-router'
import { ASSETS } from '../config/constants'

const walletStore = useWalletStore()
const router = useRouter()

const backgroundImageRight = ASSETS.landingBgRight

async function handleMetaMaskConnection() {
  const success = await walletStore.connectMetaMask()
  if (success) {
    if (walletStore.userRole === 'admin') {
      router.push({ name: 'admin' })
    } else if (walletStore.userRole === 'creator') {
      router.push({ name: 'creator' })
    }
  }
}

function handleGuestLogin() {
  walletStore.loginAsGuest()
  router.push({ name: 'public' })
}
</script>

<style scoped>
.bg-landing-light {
  background-color: #f8fafc !important;
}

.landing-content-wrapper {
  width: 100%;
  max-width: 440px;
}

.text-slate-dark {
  color: #0f172a !important;
}

.custom-title {
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  border-left: 4px solid #4f46e5; 
  padding-left: 16px;
  line-height: 1.2;
}

.subtitle-text {
  color: #475569 !important;
  line-height: 1.6;
}

.custom-guest-btn {
  border: 2px solid #cbd5e1 !important;
  color: #334155 !important;
  background-color: transparent !important;
  transition: all 0.2s ease;
}

.custom-guest-btn:hover {
  border-color: #94a3b8 !important;
  background-color: rgba(0, 0, 0, 0.02) !important;
}

.text-button {
  letter-spacing: 1px !important;
  font-size: 0.95rem !important;
}

.bg-landing-art {
  height: 100vh;
  overflow: hidden;
}

.landing-img-fluid {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.art-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(248, 250, 252, 0.2) 100%);
}
</style>