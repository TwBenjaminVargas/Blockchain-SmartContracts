import { createRouter, createWebHistory } from 'vue-router'
import { useWalletStore } from '../stores/wallet'
import Landing from '../views/Landing.vue'
import Public from '../views/Public.vue'
import Register from '../views/Register.vue'
import Admin from '../views/Admin.vue'
import Creator from '../views/Creator.vue'
import CallProposals from '../views/CallProposals.vue'
import Wallet from '../views/Wallet.vue'

const routes = [
  { path: '/', name: 'landing', component: Landing },
  { path: '/admin', name: 'admin', component: Admin, meta: { requiresRole: 'admin' } },
  { path: '/creator', name: 'creator', component: Creator, meta: { requiresRole: 'creator' } },
  { path: '/public', name: 'public', component: Public, meta: { requiresRole: 'guest' } },
  { path: '/register', name: 'register', component: Register },
  { 
    path: '/calls/:callId/proposals', 
    name: 'call-proposals', 
    component: CallProposals
  },
  { path: '/wallet', name: 'wallet', component: Wallet }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guard de navegación: Bloquea o redirige según el rol en Pinia
router.beforeEach((to, from, next) => {
  const walletStore = useWalletStore()

  if (to.meta.requiresRole && walletStore.userRole !== to.meta.requiresRole) {
    // Si intenta forzar una ruta sin el rol adecuado, lo regresa a la landing
    next({ name: 'landing' })
  } else {
    next()
  }
})

export default router