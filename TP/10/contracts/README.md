### SMART CONTRACTS (TP10) - ETAPA 1

Este directorio contiene los contratos `CFP` y `CFPFactory` junto con los artefactos de compilación generados por Hardhat.

**Cambios introducidos en este práctico (resumen)**

* Nuevo método público en la factoría: `getCreators()` que devuelve la lista completa de creadores conocidos en el ecosistema.

---

## Despliegue y compilación

### 1. Compilación de los contratos con Hardhat:

```bash
npx hardhat compile

```

### 2. Ejecución de un nodo local (Hardhat node) para desarrollo:

```bash
npx hardhat node

```

### 3. Despliegue de los contratos usando el script incluido:

```bash
node scripts/deploy.js

```

---

## Descripción detallada de `scripts/deploy.js`

El script de despliegue automatiza la configuración de dos entornos en paralelo (billeteras de testing automatizado y billeteras de interacción manual mediante MetaMask) realizando las siguientes acciones:

* **Conexión RPC:** El sistema se conecta al nodo local (por defecto `http://127.0.0.1:8545` o el valor pasado por argumento).
* **Generación del Entorno de Tests (API):** Se genera una raíz HD aleatoria y se derivan las 3 cuentas requeridas por la suite de Python: `Owner` (Index 0), `Funder` (Index 1) y `Admin` (Index 2).
* **Generación del Entorno MetaMask:** Se crea un **segundo mnemónico completamente nuevo** y se deriva su primera dirección (`Index 0`) para actuar como la cuenta del Administrador web.
* **Financiación Inicial:** Se utiliza el mnemónico por defecto de Hardhat para transferir **1000.0 ETH** a cada una de las cuentas involucradas (Owner, Funder, Admin de Test).
* **Despliegue:** Se procesa el artefacto de `CFPFactory.json` y se realiza el despliegue en la red utilizando la cuenta del `Owner` (Test Index 0).

Al completar el proceso, el script imprime bloques formateados listos para ser copiados en la configuración de la API (`api/.env`) y para la importación directa de la frase semilla en MetaMask.

---

## Scripts Adicionales: Fondeo Masivo (`scripts/fund_accounts.js`)

Para escenarios de pruebas manuales exhaustivas en el frontend donde se requiera operar con múltiples cuentas concurrentes en MetaMask, se provee un script de fondeo masivo.

Este script toma fondos de la cuenta maestra de Hardhat y distribuye **1000 ETH** a cada una de las **primeras 10 direcciones derivadas** de la frase mnemónica que se le pase por parámetro.

**Forma de uso:**

```bash
node scripts/fund_accounts.js "tu mnemónico objetivo de doce palabras aquí listado"

```

---

## Ejecución de tests (contratos)

Para ejecutar los tests unitarios de JavaScript propios de Hardhat, se deben utilizar los siguientes comandos:

```bash
npm install
npx hardhat test

```

## Estructura de archivos (resumen)

```text
contracts/
├─ contracts/
│  ├─ CFP.sol
│  └─ CFPFactory.sol
├─ scripts/
│  ├─ deploy.js
│  └─ fund_accounts.js
├─ artifacts/
│  └─ (artefactos de compilación)
└─ test/

```

---

## Notas adicionales

⚠️ **Requisito crítico:** Se debe verificar que el nodo local (`npx hardhat node`) esté ejecutándose en una terminal en segundo plano antes de iniciar cualquiera de los scripts (`deploy.js` o `fund_accounts.js`), permitiendo así que las transacciones de transferencia y despliegue puedan procesarse y confirmarse.