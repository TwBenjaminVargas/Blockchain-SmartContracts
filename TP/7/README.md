# TP 7 — Sistema Descentralizado de Llamadas a Presentación de Propuestas

## Consigna

En este trabajo práctico se implementó un **sistema descentralizado de gestión de llamadas a presentación de propuestas (Call for Proposals) en Ethereum**, compuesto por dos contratos inteligentes complementarios que implementan el ciclo de vida completo de un llamado: creación, registro de propuestas, autenticación de creadores y gestión de tiempos de cierre.

### Requisitos implementados

1. **Contrato `CFP` (Call for Proposals)**: Implementa un llamado individual donde se pueden registrar propuestas (representadas como hashes de documentos) con validaciones de tiempo de cierre y control de acceso.
2. **Contrato `CFPFactory`**: Implementa una factoría que crea instancias de contratos `CFP` y gestiona un sistema de autorización de creadores con registro pendiente.
3. **Tests automatizados**: Suite de tests que valida todos los casos de uso y validaciones de errores.

---

## Estructura de la solución

```
TP/7/
├── contracts/
│   ├── CFP.sol                        # Contrato para llamados individuales
│   └── CFPFactory.sol                 # Factoría y gestor de autorizaciones
├── test/
│   ├── testCFP.js                     # Tests del contrato CFP
│   ├── testCFPFactory.js              # Tests del contrato CFPFactory
│   └── shared.js                      # Utilidades compartidas para tests
├── hardhat.config.js                  # Configuración de Hardhat
└── package.json                       # Dependencias del proyecto
```

---

## Descripción de la Solución

### Arquitectura General

El sistema implementa un patrón de **factoría descentralizada con autorización** donde:

- **`CFP`** es un contrato individual que modela cada llamado a presentación de propuestas, controlando: identificador del llamado, timestamp de cierre, registro de propuestas y datos asociados.
- **`CFPFactory`** es la factoría que crea instancias de `CFP`, gestiona un sistema de autorización de creadores (registro → pendiente → autorizado/rechazado) y permite consultar información de llamados creados.
- Ambos contratos se comunican mediante eventos y llamadas directas para mantener consistencia en el estado global.

### Contrato `CFP`

Modela el ciclo de vida completo de un llamado a propuestas:

#### Estructuras de datos

- **`ProposalData`**: Almacena información de una propuesta registrada:
  - `address sender`: Dirección del autor de la propuesta
  - `uint blockNumber`: Número de bloque en que se registró
  - `uint timestamp`: Timestamp del registro

#### Funcionalidades principales

- **Constructor**: Recibe `bytes32 callId` y `uint closingTime` (timestamp de cierre). Valida que el cierre no esté en el pasado.
  
- **`registerProposal(bytes32 proposal)`**: Registra una propuesta como el emisor del mensaje.
  - Validaciones: Llamado no cerrado, propuesta no duplicada.
  - Emite: `ProposalRegistered`.

- **`registerProposalFor(bytes32 proposal, address sender)`**: Registra una propuesta en nombre de otro (solo creador del llamado).
  - Validaciones: Solo creador, llamado no cerrado, propuesta no duplicada.
  - Emite: `ProposalRegistered`.

- **Funciones de consulta**: `proposalData()`, `proposalCount()`, `proposals()`, `closingTime()`, `callId()`, `creator()`, `proposalTimestamp()`.

#### Eventos emitidos por `CFP`

- `ProposalRegistered(bytes32 proposal, address sender, uint blockNumber)`

#### Validaciones y errores

- `"El cierre de la convocatoria no puede estar en el pasado"`: Si `closingTime` ≤ bloque actual.
- `"Convocatoria cerrada"`: Si se intenta registrar propuesta después del cierre.
- `"La propuesta ya ha sido registrada"`: Si la propuesta ya existe.
- `"Solo el creador puede hacer esta llamada"`: Si intenta `registerProposalFor` sin autorización.

### Contrato `CFPFactory`

Factoría que gestiona la creación y autorización de llamados:

#### Estructuras de datos

- **`CallForProposals`**: Almacena información de un llamado:
  - `address creator`: Dirección del creador del llamado
  - `CFP cfp`: Instancia del contrato `CFP` creado

#### Funcionalidades principales

- **Constructor**: Registra al emisor como dueño de la factoría.

- **`create(bytes32 callId, uint timestamp)`**: Crea un nuevo llamado.
  - Validaciones: Emisor debe estar autorizado, `callId` único.
  - Retorna: Dirección del nuevo contrato `CFP`.
  - Emite: `CFPCreated`.

- **`createFor(bytes32 callId, uint timestamp, address creator)`**: Crea un llamado especificando creador (solo dueño).
  - Validaciones: Solo el dueño de la factoría.

- **`register()`**: Permite que una cuenta se registre para crear llamados.
  - Entra en estado "pendiente" hasta autorización del dueño.
  - Validaciones: No debe estar ya registrada.

- **`registerProposal(bytes32 callId, bytes32 proposal)`**: Registra una propuesta en un llamado existente.
  - Valida que el `callId` exista.

- **`authorize(address creator)`**: Autoriza a una cuenta registrada (solo dueño).
  - Si estaba pendiente, la quita de la lista de pendientes.

- **`unauthorize(address creator)`**: Desautoriza a una cuenta (solo dueño).
  - Si estaba pendiente, la quita de la lista de pendientes.

- **Funciones de consulta**: `owner()`, `calls()`, `creatorsCount()`, `creators()`, `createdByCount()`, `createdBy()`, `pendingCount()`, `getPending()`, `getAllPending()`, `isRegistered()`, `isAuthorized()`.

#### Eventos emitidos por `CFPFactory`

- `CFPCreated(address creator, bytes32 callId, CFP cfp)`

#### Validaciones y errores

- `"Solo el creador puede hacer esta llamada"`: Si intenta función restringida al dueño.
- `"El llamado ya existe"`: Si `callId` duplicado.
- `"El llamado no existe"`: Si se registra propuesta para `callId` inexistente.
- `"No autorizado"`: Si intenta crear llamado sin autorización.
- `"Ya se ha registrado"`: Si intenta registrarse nuevamente.

---

## Ejecución

### Pruebas

Desde la carpeta `TP/7`:

```bash
npm run test
```

---

## Observaciones Técnicas

### Patrones de implementación

- **Control de acceso**: Utiliza modificadores y validaciones inline para garantizar que solo usuarios autorizados ejecuten funciones críticas.
  
- **Gestión de tiempo**: Usa `block.timestamp` para validar tiempos de cierre de llamados.

- **Mapeos para búsqueda O(1)**: 
  - Mapeo de propuestas por hash en `CFP`
  - Mapeo de llamados por `callId` en `CFPFactory`

- **Listas dinámicas**: 
  - Lista de creadores registrados
  - Lista de cuentas pendientes de autorización
  - Listas de llamados creados por cada creador

### Comunicación entre contratos

- La factoría `CFPFactory` delega la creación de instancias `CFP` pero no mantiene estado sincronizado; cada llamado es independiente.
- El método `registerProposal(bytes32 callId, bytes32 proposal)` de la factoría actúa como proxy hacia el contrato `CFP` correspondiente.

### Seguridad

- Validaciones de timestamp en constructor y métodos de registro.
- Prevención de propuestas duplicadas mediante mapeos.
- Control de acceso mediante checks de `msg.sender` y modificadores.
- Mensajes de error descriptivos para facilitar debugging.

---

## Conclusión

Este TP permitió aplicar conceptos avanzados de desarrollo de contratos inteligentes: gestión compleja de estado distribuido, patrones de factoría con autorizaciones, ciclos de vida con tiempos de validez, eventos blockchain, y gestión de múltiples tipos de datos. La implementación demuestra cómo construir sistemas descentralizados que permiten a múltiples actores crear y gestionar instancias de contratos con control de autorización y validaciones temporales robustas.
