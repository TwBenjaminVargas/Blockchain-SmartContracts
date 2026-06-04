# API TP10 (ETAPA 1) — CFP API

  Este directorio contiene la implementación de la API REST que interactúa con los contratos `CFP` y `CFPFactory` y la persistencia off-chain necesaria para la etapa 1.

## Resumen de cambios principales (etapa 1)**
  
  - Migración del esquema de firma: se actualizó la lógica de firma de EIP-191 a EIP-712. Los tests y funciones auxiliares fueron adaptados para usar `eth_account.messages.encode_structured_data` y tipos EIP-712. Esto minimiza cambios en los tests puesto que las funciones helper conservan sus nombres y parámetros.
  - Nuevos endpoints añadidos / expuestos para la interfaz de administración: `GET /admin/address`, `GET /creators`, `GET /users`, `GET /users/pending`.
  Detalles de la migración de firmas
  - Antes: firmas EIP-191 (mensajes con prefijos y `encode_defunct`).
  - Ahora: firmas EIP-712 (mensajes estructurados). Se definieron `EIP712_TYPES`, un dominio dinámico (`get_eip712_domain`) y se reescribieron las funciones `make_*_message(...)` para devolver diccionarios estructurados listos para firmar.
  Impacto en tests
  - `test_apiserver.py` se actualizó para usar `encode_structured_data` y las nuevas funciones de generación y firmado. La mayor parte del cuerpo de los tests no requiere cambios adicionales.
  Endpoints añadidos y modificados
  - `POST /create` : registra en la API un llamado en estado `pending` y requiere firma EIP-712 del creador.
  - `POST /register` : registro de usuarios (sin cambios funcionales en el contrato, pero adaptado a EIP-712).
  - `GET /admin/address` : devuelve la dirección administradora usada por la interfaz.
  - `GET /creators` : lista creadores conocidos.
  - `GET /users` : lista usuarios registrados.
  - `GET /authorization-requests` : lista usuarios que esperan autorizacion del admin.
  
  
 ## Variables de entorno requeridas
  
  La API utiliza variables de entorno (ver `.env.example`). Las principales variables necesarias son:
  - `WEB3_PROVIDER_URL`: URL RPC del nodo (por defecto `http://127.0.0.1:8545`).
  - `CFP_FACTORY_ADDRESS`: dirección del contrato `CFPFactory` desplegado.
  - `CFP_MNEMONIC`: frase mnemónica usada para derivar las cuentas locales del servidor.
  - `DERIVACION_PATH`: ruta de derivación HD (por defecto `m/44'/60'/0'/0/0`).
  - `CFP_DB_PATH`: ruta al archivo SQLite usado por la API (por ejemplo `db/database.db`).
  - `CFP_ADMIN_ADDRESS`: dirección administradora usada por la aplicación.
 
 
  Incluimos un archivo `.env.example` en este directorio que muestra la estructura y valores de ejemplo. Para desarrollo, copie `.env.example` a `.env` y ajuste las variables.
  
  
  # Requisitos
  - Un nodo local compatible con Hardhat debe estar corriendo en `WEB3_PROVIDER_URL` (ej. `npx hardhat node`). La API depende de poder conectarse al RPC para leer eventos y enviar transacciones.
  - Ejecutar el servidor ASGI con Uvicorn:
  ```
  uvicorn api:app --reload --port 5000
  ```
  - Para ejecutar la suite de tests del servidor:
  ```
  CFP_MNEMONIC="<mnemonic>" CFP_FACTORY_ADDRESS="<factory>" CFP_ADMIN_ADDRESS="<admin>" pytest test_apiserver.py
  ```
    Los tests requieren que las variables de entorno `CFP_MNEMONIC`, `CFP_FACTORY_ADDRESS` y `CFP_ADMIN_ADDRESS` estén cargadas en el entorno.
  ## Base de datos (persistencia)
  
  La API usa SQLite a través de modelos `SQLModel`. Las tablas principales son `calls`, `proposals`, `users` y `sync_state`.
  Mermaid — esquema de la base de datos
  ```mermaid
  erDiagram
      CALLS {
          VARCHAR callId PK "Identificador del llamado (keccak)"
          VARCHAR title
          VARCHAR description
          VARCHAR creator
          VARCHAR state
          VARCHAR contractAddress
          INTEGER closingTime
      }
      PROPOSALS {
          VARCHAR proposalId PK "Raíz Merkle"
          VARCHAR callId FK "FK -> CALLS.callId"
          VARCHAR title
          VARCHAR titleHash
          VARCHAR description
          VARCHAR descriptionHash
          TEXT filesJson
          TEXT proofsJson
          INTEGER created
          INTEGER blocknumber
          VARCHAR sender
      }
      USERS {
          VARCHAR address PK
          VARCHAR name
          VARCHAR signature
          VARCHAR description
          VARCHAR state
          INTEGER nonce
      }
      SYNC_STATE {
          INTEGER id PK
          INTEGER last_scanned_block
      }
      CALLS ||--o{ PROPOSALS : "has"
      CALLS ||--o{ USERS : "creator_of"
  ```
### Notas sobre el diagrama
  - `proposals.callId` tiene una llave foránea hacia `calls.callId`.
  - `users.address` es la primaria y contiene estado y `nonce` para flujos de autorización.
## Estructura de directorios (resumen)
  ```
  api/
  ├─ api.py
  ├─ test_apiserver.py
  ├─ requirements.txt
  ├─ .env.example
  ├─ db/
  │  └─ sqliteManager.py
  ├─ models/
  │  ├─ persistence/
  │  │  ├─ Call.py
  │  │  ├─ Proposal.py
  │  │  ├─ SyncState.py
  │  │  └─ User.py
  ├─ requests/
  ├─ services/
  │  ├─ contractManager.py
  │  └─ signer.py
  └─ test/
  ```
  Archivos de pruebas y migración de firma
  - `test_apiserver.py` fue adaptado para EIP-712; los cambios clave incluyen: reemplazo de `encode_defunct` por `encode_structured_data`, eliminación de prefijos binarios, definición de `EIP712_TYPES`, funciones `get_eip712_domain(...)`, `make_*_message(...)` y la actualización de `sign_bytes(...)` para aceptar un dict estructurado.
  Referencias internas
  - ABI de contratos: `services/cfp_abi.json` y `services/cfp_factory_abi.json`.
  - Configuración y ajustes: `services/settings.py`.