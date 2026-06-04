import { Contract } from "ethers"
const GENERIC_BACKGROUND_URL = 'https://images.unsplash.com/photo-1518655048521-f130df041f66?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
export const ASSETS = {
  // Imágenes de fondo
  genericBg: GENERIC_BACKGROUND_URL,
  landingBg: 'https://images.unsplash.com/photo-1447069387593-a5de0862481e?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
  registerBg: GENERIC_BACKGROUND_URL,
  // Iconos SVG
  clockIcon: 'https://www.svgrepo.com/show/524426/clock-circle.svg'

}

export const URL = {
    url_base: 'http://localhost:5000',
    admin_address: '/admin/address',
    creators: '/creators',
    registrationStatus: '/registrations/:address',
    registerUser: '/register',
    contract_address: '/contract-address'
}