# Web UI (TP10) - ETAPA 1

Este directorio contiene la interfaz web del proyecto (stack: Vue 3 + Vite + Pinia). La web implementa los flujos de la etapa 1: conexión con MetaMask, registro de usuarios, panel de creadores y panel administrativo básico.

## Flujos implementados (etapa 1)

* **Conexión con MetaMask (`connectMetaMask`):** solicita `eth_requestAccounts` y guarda la cuenta en el store.
* **Registro de usuario (`/register`):** consta de un flujo híbrido de dos pasos. Primero, el usuario firma un mensaje EIP-712 (`RegisterRequest`) desde MetaMask y la app envía la firma a la API (`registerUser`). Posteriormente, se solicita al usuario firmar y enviar una transacción on-chain para ejecutar el método `register()` del smart contract factoría.
* **Edición de perfil de creador (`Creator.vue`):** el creador firma un mensaje EIP-712 de tipo `RegisterRequest` con operación `update` y envía un `PATCH /registrations/:address` a la API.
* **Panel de administración (`Admin.vue`):** el administrador firma órdenes EIP-712 (`AdminActionRequest`) para `authorize` / `unauthorize`, y la app envía la firma a la API.

## Operaciones On-chain vs Off-chain (MetaMask y API)

* **Operaciones On-chain (Blockchain mediante MetaMask):**
* `eth_requestAccounts` para conectar y obtener la cuenta activa del usuario.
* Envío y firma de transacciones nativas para interactuar con los métodos de los Smart Contracts (ej. ejecución de `register()` en el contrato de la factoría).


* **Operaciones Off-chain (Mensajes firmados y Requests HTTP a la API):**
* **Firmas criptográficas en cliente (`signTypedData` - EIP-712):**
* Registro (`RegisterRequest`) — `operation: "register"`.
* Actualización de perfil (`RegisterRequest` con `operation: "update"`).
* Acciones administrativas (`AdminActionRequest`) — `operation: "authorize"` o `"unauthorize"`.


* **Llamadas HTTP a la API REST:**
* Obtener datos públicos y de estado: `GET /admin/address`, `GET /creators`, `GET /users`, `GET /users/pending`, `GET /admin/nonce`, `GET /contract/address`.
* Registrar/actualizar usuarios en base de datos: `POST /register`, `PATCH /registrations/:address` (el payload contiene la firma EIP-712).
* Acciones administrativas: `POST /authorize/:address`, `POST /unauthorize/:address` (payload con `signature`).





## Cómo la web usa la API

* La capa `src/services/api.js` centraliza las llamadas a la API.
* El `wallet store` (`src/stores/wallet.js`) consulta `getAdminAddress` y `getRegistrationStatus` para asignar roles (`admin`, `creator`, `guest`, `pending`).
* Los componentes usan `signTypedData` para generar firmas EIP-712 y envían las firmas a la API en los endpoints correspondientes.

## Puesta en marcha local

1. Instalar dependencias:

```bash
cd web
npm install

```

2. Ejecutar en modo desarrollo:

```bash
npm run dev

```

URL por defecto: `http://localhost:5173` (Vite).

## Estructura de directorios (resumen)

```
web/
├─ package.json
├─ index.html
├─ src/
│  ├─ main.js
│  ├─ App.vue
│  ├─ router/
│  ├─ services/
│  │  └─ api.js
│  ├─ stores/
│  │  └─ wallet.js
│  └─ views/
│       ├─ Admin.vue
│       ├─ Creator.vue
│       └─ Register.vue
└─ public/

```

## Notas

* El frontend espera que la API esté disponible y que el contrato factoría esté desplegado (la API provee `GET /admin/address` y `GET /contract/address`).
* Todas las interacciones que requieren una firma o el pago de gas se realizan exclusivamente a través de MetaMask.