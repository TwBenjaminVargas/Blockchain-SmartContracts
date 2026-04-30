# TP 6 — Sistema Descentralizado de Gestión de Tareas

## Consigna

En este trabajo práctico se implementó un **sistema descentralizado de gestión de tareas en Ethereum**, compuesto por dos contratos inteligentes complementarios que implementan un ciclo de vida completo de tareas: creación, asignación, progreso y finalización.

### Requisitos implementados

1. **Contratos `TaskBoard` y `Task`**: Implementados de acuerdo a especificaciones, pasando todos los casos de prueba. Todos los requisitos se especificaron mediante modificadores (_modifiers_).
2. **Función `listTasksByAssignee()`**: Implementada en el script `list-tasks-by-assignee.js` para consultar tareas filtradas por responsable asignado y estado, con múltiples opciones de lectura de timestamps.

---

## Estructura de la solución

```
TaskSystem/
├── contracts/
│   ├── Task.sol                    # Contrato para tareas individuales
│   └── TaskBoard.sol               # Factoría y gestor de estados
├── scripts/
│   ├── deploy.js                   # Script de despliegue básico
│   ├── deploy-with-sample-data.js  # Script con datos de ejemplo
│   └── list-tasks-by-assignee.js   # Consulta de tareas por responsable
├── test/
│   ├── TaskSystem.js               # Tests de contratos
│   └── list-tasks-by-assignee.unit.test.js  # Tests de script
├── hardhat.config.js               # Configuración de Hardhat
└── package.json                    # Dependencias del proyecto
```

---

## Descripción de la Solución

### Arquitectura General

El sistema implementa un patrón de **factoría descentralizada** donde:

- **`TaskBoard`** es el contrato factoría que crea instancias de `Task` y gestiona su ciclo de vida a través de tres listas de estados.
- **`Task`** es un contrato individual que modela cada tarea, controlando su descripción, responsables y cambios de estado.
- Ambos contratos se comunican mediante la interface `ITaskRegistry` para mantener consistencia en el estado global.

### Contrato `Task`

Modela el ciclo de vida completo de una tarea individual:

#### Estados internos
- **ToDo (Pendiente)**: Tarea creada, esperando asignación y comienzo.
- **InProgress**: Trabajador ha iniciado la resolución.
- **Completed**: Tarea finalizada.

#### Funcionalidades principales

- `assign(address worker)`: Permite que el solicitante asigne la tarea a un trabajador.
  - Requisitos: Solo el reporter, solo si está en estado ToDo.
  - Emite: `TaskAssigned`.

- `start()`: Permite que el trabajador asignado inicie la tarea.
  - Requisitos: Solo el assignee, solo si está en estado ToDo.
  - Notifica a la factoría y emite: `TaskStarted`.

- `complete()`: Marca la tarea como completada.
  - Requisitos: Solo el assignee, solo si está en progreso.
  - Notifica a la factoría y emite: `TaskCompleted`.

- Funciones de consulta: `description()`, `reporter()`, `assignee()`, `started()`, `completed()`, `assignedAt()`, `startedAt()`, `completedAt()`.

#### Eventos emitidos por `Task`

- `TaskAssigned(address reporter, address assignee, uint256 timestamp)`
- `TaskStarted(address assignee, uint256 timestamp)`
- `TaskCompleted(address assignee, uint256 timestamp)`

### Contrato `TaskBoard`

Factoría que gestiona el ciclo de vida de todas las tareas:

#### Gestión de estado
Mantiene tres listas de tareas (`todo`, `inProgress`, `done`) que se actualizan automáticamente cuando:
- Se crea una nueva tarea → entra en `todo`.
- Un trabajador inicia una tarea → pasa a `inProgress`.
- Se completa una tarea → pasa a `done`.

#### Funcionalidades principales

- `createTask(string memory description)`: Crea una nueva instancia de `Task`.
  - Retorna la dirección del contrato creado.
  - Emite: `TaskCreated`.

- Contadores: `todoCount()`, `inProgressCount()`, `doneCount()`.

- Filtrado por responsable asignado:
  - `todoByAssignee(address worker)`: Devuelve tareas en ToDo asignadas a un trabajador.
  - `inProgressByAssignee(address worker)`: Tareas en InProgress.
  - `doneByAssignee(address worker)`: Tareas completadas.

- `taskStarted()` y `taskCompleted()`: Métodos de la interface `ITaskRegistry` que son invocados por los contratos `Task` para notificar cambios de estado.

#### Eventos emitidos por `TaskBoard`

- `TaskCreated(address taskAddress, address reporter, string description)`
- `TaskMovedToInProgress(address taskAddress, uint256 index)`
- `TaskMovedToDone(address taskAddress, uint256 index)`

### Script `listTasksByAssignee.js`

Herramienta de consulta que permite:

- Filtrar tareas por: estado (pending/in-progress/done), responsable asignado.
- Obtener timestamps de dos formas:
  - **contract**: Lectura directa de variables de estado del contrato.
  - **events**: Inferencia desde eventos emitidos en blockchain.
- Salida en formato JSON con información completa de cada tarea.

---

## Ejecución

### Compilación y pruebas

Desde la carpeta `TP/6/TaskSystem`:

```bash
# Compilar contratos
npx hardhat compile

# Ejecutar tests
npx hardhat test
```

### Despliegue

#### Despliegue básico (solo TaskBoard)

```bash
npm run deploy
```

El comando imprime la dirección del contrato desplegado.

#### Despliegue con datos de ejemplo

```bash
npm run deploy:sample
```

Despliega `TaskBoard`, crea tareas de ejemplo en diferentes estados e imprime direcciones clave:
- `TASKBOARD_ADDRESS`
- `ASSIGNEE_1`, `ASSIGNEE_2`, `ASSIGNEE_3`

Para la red `localhost` (recomendado con `npx hardhat node`):

```bash
npm run deploy:sample:localhost
```

### Consulta de tareas

```bash
npm run list-tasks -- \
  --board <TASKBOARD_ADDRESS> \
  --assignee <WORKER_ADDRESS> \
  --state <pending|in-progress|done> \
  --timestamps <contract|events> \
  [--rpc <RPC_URI>]
```

**Parámetros:**
- `--board`: Dirección del contrato `TaskBoard`.
- `--assignee`: Dirección del responsable asignado a consultar.
- `--state`: Estado de las tareas (`pending`, `in-progress` o `done`).
- `--timestamps`: Fuente de timestamps (`contract` para leer del estado, `events` para inferir desde eventos).
- `--rpc` (opcional): URI JSON-RPC. Por defecto: `http://localhost:8545`.

#### Ejemplo completo

```bash
# En una terminal: iniciar nodo local
npx hardhat node

# En otra terminal: desplegar con datos
npm run deploy:sample:localhost

# Consultar tareas completadas con timestamps del contrato
npm run list-tasks -- \
  --board 0x5FbDB2315678afecb367f032d93F642f64180aa3 \
  --assignee 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 \
  --state done \
  --timestamps contract
```

---
## Observaciones Técnicas

### Control de acceso

Todos los requisitos se implementaron mediante modificadores (_modifiers_):
- `reporterRequired`: Valida que solo el solicitante pueda actuar.
- `assigneeRequired`: Valida que solo el asignado pueda actuar.
- `pendingStateRequired`: Valida que la tarea esté en estado ToDo.
- `inProgressStateRequired`: Valida que la tarea esté en progreso.

### Eficiencia de almacenamiento

- Se usa un mapping (`tasks`) para acceso O(1) a información de cada tarea.
- Se mantienen índices en las listas para operación O(1) de remoción (usando "swap and pop").
- Las listas de tareas filtradas por responsable se construyen on-chain para garantizar consistencia.

### Comunicación contrato-factoría

- Los contratos `Task` invocan `taskStarted()` y `taskCompleted()` de la factoría.
- La factoría valida que el llamante sea una tarea registrada antes de actualizar estado.

### Mensajes de error

Se implementaron validaciones con mensajes descriptivos:
- `"Solo el reporter puede realizar esta accion"`: Cuando alguien que no es el solicitante intenta actuar.
- `"Solo el assignee puede realizar esta accion"`: Cuando alguien que no es el asignado intenta actuar.
- `"La tarea ya ha comenzado"`: Cuando se intenta asignar una tarea ya iniciada.
- `"La tarea no esta en progreso"`: Cuando se intenta completar una tarea que no está en progreso.

---

## Conclusión

Este TP permitió aplicar conceptos fundamentales de desarrollo de contratos inteligentes: gestión compleja de estado distribuido, patrones de factoría, comunicación entre contratos, eventos blockchain, y herramientas de consulta. La implementación demuestra cómo construir sistemas descentralizados que mantienen consistencia entre múltiples contratos y permiten consultas eficientes de estado.
