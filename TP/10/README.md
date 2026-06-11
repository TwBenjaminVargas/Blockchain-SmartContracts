# Trabajo Práctico 10 (ETAPA 1) — Resumen y puesta en marcha

Este repositorio reúne los tres componentes del TP10:

* `contracts/` — smart contracts (Hardhat).
* `api/` — servidor REST (Python/ASGI) y persistencia SQLite.
* `web/` — interfaz frontend (Vue 3 + Vite).

Los READMEs de cada subdirectorio contienen la documentación detallada. Aquí se ofrece una guía rápida de puesta en marcha local para la etapa 1.
Puede usarse una estructura de directorios diferente si las herramientas utilizadas así lo requieren. En este caso se deberá indicar claramente en qué directorio se encuentra cada uno de los tres componentes.

## Descripción general

Debe proveerse un sistema de gestión de llamados a presentación de propuestas, con los criterios utilizados en los prácticos 7, 8 y 9.

Este práctico requiere modificaciones tanto en los contratos como en la API, además del desarrollo de una interfaz web completa.


## Puesta en marcha rápida (local)

### 1) Instalar dependencias de los tres componentes:

```bash
# Contratos (node)
cd contracts
npm install

# API (Python, virtualenv recomendado)
cd ../api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Web (node)
cd ../web
npm install

```

### 2) Ejecutar un nodo local Hardhat (nuevo terminal):

```bash
cd contracts
npx hardhat node

```

### 3) Compilar y desplegar contratos (en otro terminal):

```bash
cd contracts
npx hardhat compile
node scripts/deploy.js

```

El script `scripts/deploy.js` automatiza las siguientes tareas:

* Genera un **mnemónico aleatorio para la suite de pruebas** (Python) y deriva las cuentas requeridas (`Owner` en Index 0, `Funder` en Index 1 y `Admin` en Index 2).
* Genera un **segundo mnemónico exclusivo para MetaMask**, configurando la cuenta de Administrador en la primera dirección derivable (`Index 0`) para facilitar su uso en la interfaz web.
* Despliega `CFPFactory` e imprime bloques de texto listos para copiar y pegar con las configuraciones del entorno.

### 4) Configurar variables para la API

Copiar `api/.env.example` a `api/.env` y completar las variables utilizando el bloque **CONFIGURACIÓN DE TESTS (API)** o el bloque **CONFIGURACIÓN METAMASK** impreso en la consola por el script de despliegue:

```ini
WEB3_PROVIDER_URL=http://127.0.0.1:8545
CFP_FACTORY_ADDRESS=<dirección_de_factory>
CFP_MNEMONIC="<CFP_MNEMONIC del owner>"
DERIVACION_PATH="m/44'/60'/0'/0/0"
CFP_DB_PATH="db/database.db"
CFP_ADMIN_ADDRESS="<CFP_ADMIN_ADDRESS para tests o de metamask>"

```

### 5) Ejecutar API (virtualenv activado):

```bash
cd api
uvicorn api:app --reload --port 5000

```

### 6) Ejecutar frontend:

```bash
cd web
npm run dev

```

URL por defecto: `http://localhost:5173` (Vite).

💡 **Nota para el uso de MetaMask:** Al abrir la aplicación web importar el mnemónico generado bajo la sección **CONFIGURACIÓN METAMASK** que se mostró al ejecutar el despliegue. La primera dirección derivable (`Index 0`) será la cuenta de Administrador web.

### 7) Ejecutar tests de la API

Los tests de la API requieren las variables de entorno de la suite de pruebas exportadas en la terminal. Se pueden utilizar los valores exactos arrojados en la consola por el script de despliegue:

```bash
CFP_MNEMONIC="<test_mnemonic>" CFP_FACTORY_ADDRESS="<factory_address>" CFP_ADMIN_ADDRESS="<test_admin_address>" pytest test_apiserver.py

```
⚠️ **Condición Crítica de Derivación:** Las direcciones asignadas a las pruebas deben cumplir estrictamente la condición de coexistencia criptográfica. Es decir, tanto el `Owner` (`Index 0`) como el `Admin` (`Index 2`) **deben ser derivados de la misma frase mnemónica** (`CFP_MNEMONIC`). De lo contrario, las firmas estructuradas EIP-712 y las verificaciones de permisos fallarán en la API.
---

## Scripts Adicionales de Utilidad

### Fondeo Masivo de Cuentas (`scripts/fund_accounts.js`)

En caso de requerir pruebas manuales exhaustivas con múltiples cuentas derivadas, se incluye un script que toma fondos de la cuenta por defecto de Hardhat y transfiere **1000 ETH** a cada una de las primeras 10 direcciones derivadas de un mnemónico específico.

**Forma de uso:**

```bash
cd contracts
node scripts/fund_accounts.js "tu mnemónico objetivo de doce palabras aquí listado"

```

---

## Notas importantes

* **Migración de firmas:** la API y los tests fueron adaptados de EIP-191 a EIP-712. Las firmas ahora usan mensajes estructurados y el dominio:

```json
{
  "name": "CFP API",
  "version": "1",
  "chainId": 31337,
  "verifyingContract": "<dirección del contrato CFPFactory>"
}

```

* **Consultar los README de cada subdirectorio para documentación específica:**
* `contracts/README.md` — compilación, scripts de despliegue y detalles de la arquitectura blockchain.
* `api/README.md` — endpoints, variables de entorno, esquema de la base de datos (Mermaid) y guía para tests.
* `web/README.md` — flujos implementados, guías de uso de MetaMask y comandos para desarrollo.