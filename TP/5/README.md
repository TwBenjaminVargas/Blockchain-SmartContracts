# TP 5 — Contrato Inteligente de Votación

## Consigna

En este trabajo práctico se implementó un **contrato inteligente de votación** (Ballot) en Solidity. El contrato gestiona un proceso electoral completo, permitiendo que un presidente designe votantes, controle el inicio y cierre de la votación, y calcule automáticamente las propuestas ganadoras.

## Estructura de la solución

```
Ballot/
├── contracts/
│   └── Ballot.sol              # Contrato inteligente de votación
├── scripts/
│   └── deploy.js               # Script de despliegue del contrato
├── test/
│   └── ballot.test.js          # Tests unitarios del contrato
├── hardhat.config.js           # Configuración de Hardhat
└── package.json                # Dependencias del proyecto
```

---

## Descripción del Contrato Ballot

### Objetivo

Implementar un sistema de votación descentralizado en Ethereum que permita:
- Un **presidente** controlar el proceso electoral
- Designar direcciones con derecho a votar
- Retirar derechos de voto antes de iniciar la votación
- Gestionar el inicio y cierre del período de votación
- Calcular automáticamente las propuestas ganadoras, incluyendo casos de empate

### Estructura de datos

El contrato utiliza dos estructuras principales:

#### `Voter`
- `canVote`: booleano indicando si el votante tiene derecho a votar
- `voted`: booleano indicando si ya ha votado
- `vote`: índice de la propuesta elegida

#### `Proposal`
- `name`: nombre de la propuesta (hasta 32 bytes)
- `voteCount`: cantidad de votos recibidos

### Funcionalidades principales

#### 1. **Gestión de derechos de voto**
- `giveRightToVote(address voter)`: otorga derecho a votar a una dirección
- `withdrawRightToVote(address voter)`: retira el derecho de voto
- `giveAllRightToVote(address[] memory list)`: otorga derechos a múltiples direcciones simultáneamente

#### 2. **Control del proceso electoral**
- `start()`: inicia la votación (solo presidente)
- `started()`: consulta si la votación ha comenzado
- `end()`: finaliza la votación (solo presidente)
- `ended()`: consulta si la votación ha finalizado

#### 3. **Votación**
- `vote(uint proposal)`: emite el voto por una propuesta específica
  - Valida que el votante tenga derecho a votar
  - Valida que no haya votado previamente
  - Valida que la votación esté activa
  - Valida que la propuesta sea válida

#### 4. **Resultados**
- `winningProposals()`: devuelve un array con los índices de las propuestas ganadoras
  - Solo se ejecuta después de finalizar la votación
  - Maneja correctamente casos de empate
  - Devuelve un array vacío si no hay votos

#### 5. **Consultas**
- `numProposals()`: devuelve la cantidad de propuestas
- `numVoters`: almacena la cantidad total de votantes autorizados
- `chairperson`: dirección del presidente que controla el proceso
- `voters[address]`: información de cada votante
- `proposals[uint]`: información de cada propuesta

### Observaciones técnicas

- El contrato implementa control de acceso: solo el presidente puede autorizar votantes e iniciar/finalizar la votación
- Previene vulnerabilidades comunes como votación doble mediante flags `voted`
- La función `winningProposals()` maneja correctamente empates, devolviendo todas las propuestas con la máxima cantidad de votos
- Validaciones exhaustivas en cada función crítica para asegurar integridad del proceso electoral

---

## Ejecución

### Compilación y ejecución de tests
Desde la carpeta `TP/5/Ballot`:

```bash
# Compilar el contrato
npx hardhat compile

# Ejecutar los tests
npx hardhat test
```

### Tests incluidos

El archivo `ballot.test.js` contiene pruebas exhaustivas que verifican:
- Validaciones en el despliegue
- Gestión correcta de derechos de voto
- Inicio y finalización del proceso electoral
- Emisión de votos y validaciones
- Cálculo correcto de propuestas ganadoras, incluyendo empates

---

## Conclusión

En este TP se aplicaron conceptos fundamentales de desarrollo de contratos inteligentes en Ethereum: gestión de estado, control de acceso, validaciones de seguridad y lógica de negocio compleja. La implementación permite observar cómo Solidity maneja estructuras de datos, mappings y arrays dinámicos en un contexto práctico de aplicación descentralizada.
