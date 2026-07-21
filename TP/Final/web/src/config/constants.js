import { Contract } from "ethers"
import { authorizeUser, getCallContractAdress, getTokenAddress, updateRegistration } from "../services/api"
const GENERIC_BACKGROUND_URL = 'https://images.unsplash.com/photo-1518655048521-f130df041f66?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
export const ASSETS = {
  // Imágenes de fondo
  genericBg: GENERIC_BACKGROUND_URL,
  landingBg: 'https://images.unsplash.com/photo-1447069387593-a5de0862481e?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
  registerBg: GENERIC_BACKGROUND_URL,
  adminBg: GENERIC_BACKGROUND_URL,
  creatorBg: GENERIC_BACKGROUND_URL,
  callsProposalsBg: GENERIC_BACKGROUND_URL,
  // Iconos SVG
  clockIcon: 'https://www.svgrepo.com/show/524426/clock-circle.svg',
  questionIcon: 'https://www.svgrepo.com/show/509211/question.svg',
  pencilIcon: 'https://www.svgrepo.com/show/489772/pencil.svg',
  exitIcon: 'https://www.svgrepo.com/show/343096/exit-left.svg'

}
import FactoryAbi from '../abis/CFPFactory.json'
import RegistryAbi from '../abis/Registry.json'
import ResolverAbi from '../abis/Resolver.json'
import UsuariosRegistrarAbi from '../abis/UsuariosRegistrar.json'
import LlamadosRegistrarAbi from '../abis/LlamadosRegistrar.json'
import ReverseRegistrarAbi from '../abis/ReverseRegistrar.json'
export const FILES = 
{
  CFP_FACTORY_ABI: FactoryAbi,
  REGISTRY_ABI: RegistryAbi,
  RESOLVER_ABI: ResolverAbi,
  USUARIOS_REGISTRAR_ABI: UsuariosRegistrarAbi,
  LLAMADOS_REGISTRAR_ABI: LlamadosRegistrarAbi,
  REVERSE_REGISTRAR_ABI: ReverseRegistrarAbi
}

export const ENSDomains = {
  usuarios: 'usuarios.cfp',
  llamados: 'llamados.cfp',
  addrReverse: 'addr.reverse'
}

export const URL = {
    url_base: 'http://localhost:5000',
    admin_address: '/admin/address',
    creators: '/creators',
    registrationStatus: '/registrations/:address',
    registerUser: '/register',
    contract_address: '/contract-address',
    admin_nonce: '/admin/nonce',
    authorization_requests: '/authorization-requests',
    authorizeUser: '/authorize/:address',
    unauthorizeUser: '/unauthorize/:address',
    users: '/users',
    updateRegistration: `/registrations/:address`,
    getUserCalls: '/calls-by/:address',
    createCall: '/create',
    global_calls: '/global-calls',
    getProposalsByCall: '/calls/:call_id/proposals',
    getProposalReceipt: '/proposals/:proposalId/receipt',
    submitPostClosing: '/proposals/submit-post-closing',
    verifyProposal: '/proposals/verify-receipt',
    downloadProposalFiles: '/proposals/:proposal_id/download',
    getCallById: '/calls/:call_id',
    getClosingTime: '/closing-time/:call_id',
    registerProposal: '/register-proposal',
    getProposalReceiptPostClosing: '/proposals/:proposal_id/reception-receipt',
    getENSAddresses: '/ens-addresses',
    getCallContractAdress: '/calls/:call_id/contract',
    getTokenAddress: '/token-address'
}