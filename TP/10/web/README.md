# Web UI TP10 (ETAPA 1 y 2)

Este directorio contiene la interfaz web del proyecto (stack: Vue 3 + Vite + Pinia). La web implementa los flujos de la etapa 1: conexión con MetaMask, registro de usuarios, panel de creadores y panel administrativo básico.

## Flujos implementados (etapa 1)

* **Conexión con MetaMask (`connectMetaMask`):** solicita `eth_requestAccounts` y guarda la cuenta en el store.
* **Registro de usuario (`/register`):** consta de un flujo híbrido de dos pasos. Primero, el usuario firma un mensaje EIP-712 (`RegisterRequest`) desde MetaMask y la app envía la firma a la API (`registerUser`). Posteriormente, se solicita al usuario firmar y enviar una transacción on-chain para ejecutar el método `register()` del smart contract factoría.
* **Edición de perfil de creador (`Creator.vue`):** el creador firma un mensaje EIP-712 de tipo `RegisterRequest` con operación `update` y envía un `PATCH /registrations/:address` a la API.
* **Panel de administración (`Admin.vue`):** el administrador firma órdenes EIP-712 (`AdminActionRequest`) para `authorize` / `unauthorize`, y la app envía la firma a la API.

## Flujos implementados (etapa 2)
Aquí tienes la documentación actualizada de los **Flujos Implementados** que incluye detalladamente toda la arquitectura híbrida (On-Chain y Off-Chain) de las convocatorias (**Calls**) que estuvimos trabajando para las tres vistas del sistema (Administración, Creador y Pública):
* **Sincronización Híbrida del Catálogo Global (`getGlobalCalls`):** Implementado tanto en la **Vista de Administración** como en la **Vista Pública**. El sistema consume un endpoint unificado que consolida dos universos de datos:
    1) **Base Local (Internal):** Convocatorias con metadatos enriquecidos (título, descripción extendida) persistidos en la base de datos relacional de la API que mapean ciclos de vida locales (`PENDING`, `CREATED`).
    2) **Blockchain Pura (External):** Convocatorias detectadas directamente desde los nodos de la red distribuidos a través del Smart Contract Factoría, las cuales residen únicamente de forma on-chain y no cuentan con metadatos guardados en la API.

* **Estructura y Multi-Filtros Cruzados en Tiempo Real:** Las interfaces de llamados aplican una lógica reactiva mediante propiedades computadas (`computed`) que unifican ambas fuentes de datos, permitiendo búsquedas avanzadas y combinadas.
    1)  **Filtro por Palabras Clave (`searchQuery`):** Indexación instantánea en el cliente por Título, ID de la convocatoria (`callId`) o dirección física del contrato inteligente desplegado.
    2)  **Filtro por Dirección de Creador (`searchCreator`):** Entrada de texto dedicada para aislar o buscar llamados pertenecientes a una Wallet de creador específica (`0x...`), aislando los criterios de la barra de búsqueda principal para evitar colisiones semánticas.
    3) **Filtro por Estado Operacional (`filterState`):** Segmentación por procedencia del dato (`internal` vs `external`) o por el estado del ciclo de vida de la convocatoria local (`CREATED`, `PENDING`).
    4) **Filtro por Línea de Tiempo / Vigencia (`filterTimeline`):** Comparación matemática en tiempo real entre el Unix Timestamp de cierre (`closingTime`) provisto por el contrato inteligente y el tiempo UNIX del sistema (`Date.now()`), permitiendo discriminar llamados **Vigentes/Abiertos** de aquellos **Expirados/Cerrados**.
* **Creación de Convocatorias (Flujo del Creador):** Interfaz que restringe la acción exclusivamente a usuarios autorizados con rol de `creator`, orquestando la firma de metadatos off-chain con el posterior despliegue físico del contrato CFP en la Blockchain.
---

## Operaciones On-chain vs Off-chain (MetaMask y API)

* **Operaciones On-chain (Blockchain mediante MetaMask):**
* `eth_requestAccounts` para conectar y obtener la cuenta activa del usuario.
* Envío y firma de transacciones nativas para interactuar con los métodos de los Smart Contracts:
        * ejecución de `register()` en el contrato de la factoría
        * ejecucion de `create()` en el contrato de la factoría



* **Operaciones Off-chain (Mensajes firmados y Requests HTTP a la API):**
* **Firmas criptográficas en cliente (`signTypedData` - EIP-712):**
* Registro (`RegisterRequest`) — `operation: "register"`.
* Actualización de perfil (`RegisterRequest` con `operation: "update"`).
* Acciones administrativas (`AdminActionRequest`) — `operation: "authorize"` o `"unauthorize"`.
* Creacion de llamados en API


* **Llamadas HTTP a la API REST:**
* Obtener datos públicos y de estado: `GET /admin/address`, `GET /creators`, `GET /users`, `GET /users/pending`, `GET /admin/nonce`, `GET /contract/address`.
* Registrar/actualizar usuarios en base de datos: `POST /register`, `PATCH /registrations/:address` (el payload contiene la firma EIP-712).
* Acciones administrativas: `POST /authorize/:address`, `POST /unauthorize/:address` (payload con `signature`).
* Obtener datos de llamados: `GET /calls-by/address`, `GET /calls-by/address`.
* Creacion de llamados: `POST /create`


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