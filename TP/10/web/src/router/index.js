import { createRouter, createWebHistory } from 'vue-router'
import { useWalletStore } from '../stores/wallet'
import Landing from '../views/Landing.vue'
import Public from '../views/Public.vue'

// TODO Reemplazar por los views correspondiente
const AdminDashboard = { template: '<v-container><h1>Admin Dashboard</h1></v-container>' }
const CreatorDashboard = { template: '<v-container><h1>Creator Dashboard</h1></v-container>' }
const CreatorsList = { template: '<v-container><h1>Listado de Creadores (Invitado)</h1></v-container>' }

const routes = [
  { path: '/', name: 'landing', component: Landing },
  { path: '/admin', name: 'admin', component: AdminDashboard, meta: { requiresRole: 'admin' } },
  { path: '/creator', name: 'creator', component: CreatorDashboard, meta: { requiresRole: 'creator' } },
  { path: '/public', name: 'public', component: Public, meta: { requiresRole: 'guest' } }
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