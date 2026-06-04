# Trabajo Práctico 10 (ETAPA 1) — Resumen y puesta en marcha

Este repositorio reúne los tres componentes del TP10:

- `contracts/` — smart contracts (Hardhat).
- `api/` — servidor REST (Python/ASGI) y persistencia SQLite.
- `web/` — interfaz frontend (Vue 3 + Vite).

Los READMEs de cada subdirectorio contienen la documentación detallada. Aquí se ofrece una guía rápida de puesta en marcha local para la etapa 1.
Puede usarse una estructura de directorios diferente si las herramientas utilizadas así lo requieren. En este caso se deberá indicar claramente en qué directorio se encuentra cada uno de los tres componentes.

## Descripción general

Debe proveerse un sistema de gestión de llamados a presentación de propuestas, con los criterios utilizados en los prácticos 7, 8 y 9.
Este práctico requiere modificaciones tanto en los contratos como en la API, además del desarrollo de una interfaz web completa. Si se agregan nuevos métodos o *endpoints* se deberá proveer lo siguiente:

* Documentación que especifique funcionalidad, argumentos, valores devueltos y condiciones de error, ya sea como comentarios en el código o en el `README.md` correspondiente.
* Documentación del esquema de base de datos *off-chain* utilizado (tablas/colecciones, campos, claves, restricciones y relaciones).
* Casos de prueba

## Puesta en marcha rápida (local)

1) Instalar dependencias de los tres componentes:

```
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

2) Ejecutar un nodo local Hardhat (nuevo terminal):

```
cd contracts
npx hardhat node
```

3) Compilar y desplegar contratos (en otro terminal):

```
cd contracts
npx hardhat compile
npx run scripts/deploy.js
```

El script `scripts/deploy.js` deriva cuentas desde un mnemónico temporal, financia las cuentas en la red local y despliega `CFPFactory`. Al terminar imprime variables útiles para el entorno, por ejemplo `CFP_FACTORY_ADDRESS`, `CFP_MNEMONIC` y `CFP_ADMIN_ADDRESS`.

4) Configurar variables para la API

Copiar `api/.env.example` a `api/.env` y completar las variables con los valores impresos por `deploy.js` (o con los que uses en tu red):

```
WEB3_PROVIDER_URL=http://127.0.0.1:8545
CFP_FACTORY_ADDRESS=<dirección_de_factory>
CFP_MNEMONIC="<mnemonic_deploy>"
DERIVACION_PATH="m/44'/60'/0'/0/0"
CFP_DB_PATH="db/database.db"
CFP_ADMIN_ADDRESS="<admin_address>"
```

5) Ejecutar API (virtualenv activado):

```
cd api
uvicorn api:app --reload --port 5000
```

6) Ejecutar frontend:

```
cd web
npm run dev
```

URL por defecto: `http://localhost:5173` (Vite).

7) Ejecutar tests de la API

Los tests de la API requieren las variables de entorno `CFP_MNEMONIC`, `CFP_FACTORY_ADDRESS` y `CFP_ADMIN_ADDRESS` exportadas en el entorno. Ejemplo (bash):

```
CFP_MNEMONIC="<mnemonic>" CFP_FACTORY_ADDRESS="<factory>" CFP_ADMIN_ADDRESS="<admin>" pytest test_apiserver.py
```

## Notas importantes

- Migración de firmas: la API y los tests fueron adaptados de EIP-191 a EIP-712. Las firmas ahora usan mensajes estructurados y el dominio:

```
{
  "name": "CFP API",
  "version": "1",
  "chainId": <id de la cadena>,
  "verifyingContract": "<dirección del contrato CFPFactory>"
}
```

- Consultar los README de cada subdirectorio para documentación específica:

  - `contracts/README.md` — compilación, scripts de despliegue y cambios en los contratos (ej. `getCreators`).
  - `api/README.md` — endpoints, variables de entorno, esquema de la base de datos (Mermaid) y guía para tests.
  - `web/README.md` — flujos implementados, uso de MetaMask y comandos para desarrollo.

