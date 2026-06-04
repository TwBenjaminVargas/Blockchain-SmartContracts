# Smart contracts (TP10)

Este directorio contiene los contratos `CFP` y `CFPFactory` y los artefactos generados por Hardhat.

**Cambios introducidos en este práctico (resumen)**

- Nuevo método público en la factoría: `getCreators()` que devuelve la lista completa de creadores conocidos.

Despliegue y compilación

1. Compilar los contratos con Hardhat:

```
npx hardhat compile
```

2. Ejecutar un nodo local (Hardhat node) para desarrollo:

```
npx hardhat node
```

3. Desplegar los contratos usando el script incluido:

```
npx run scripts/deploy.js
```

 El script `scripts/deploy.js` genera una frase mnemónica de prueba, financia las cuentas derivadas en la red local y despliega `CFPFactory` usando la cuenta `owner` (derivada del mnemónico). Al completar imprime variables de entorno útiles:

- `CFP_FACTORY_ADDRESS`: dirección del contrato desplegado.
- `CFP_MNEMONIC`: frase mnemónica generada para la sesión de pruebas.
- `CFP_ADMIN_ADDRESS`: dirección derivada del índice 2 (administrador).

Descripción breve de `scripts/deploy.js`

- Conecta al RPC indicado (por defecto `http://127.0.0.1:8545`).
- Deriva una raíz HD aleatoria y obtiene tres cuentas: `owner` (index 0), `funder` (index 1) y `admin` (index 2).
- Usa una cuenta pre-financiada local (mnemonic por defecto Hardhat) para transferir ETH a las cuentas derivadas.
- Lee el artefacto `artifacts/contracts/CFPFactory.sol/CFPFactory.json` y despliega el contrato con `owner`.
- Imprime las variables de entorno necesarias para ejecutar la API y los tests.

Ejecución de tests (contratos)

- Para ejecutar los tests de JavaScript/Hardhat:

```
npm install
npx hardhat test
```

Estructura de archivos (resumen)

```
contracts/
├─ contracts/
│  ├─ CFP.sol
│  └─ CFPFactory.sol
├─ scripts/
│  └─ deploy.js
├─ artifacts/
│  └─ (artefactos de compilación)
└─ test/
```

Notas adicionales

- Asegúrate de lanzar `npx hardhat node` antes de ejecutar `node scripts/deploy.js` para que las transacciones puedan confirmarse en la red local.
- El script crea y muestra un mnemónico de sesión: si usas las direcciones que imprime, ajústalas en la API (`.env`) para que el servidor firme y pruebe flujos locales.
