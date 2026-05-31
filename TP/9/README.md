# Trabajo práctico 9

Este práctico integra los contratos del sistema de llamados a propuestas con una API REST y una base de datos SQLite para almacenar información fuera de la cadena. La idea central es que la cadena conserve solo lo mínimo necesario para verificar integridad, mientras que la información descriptiva y operativa quede disponible off chain.

## Qué se hizo

Se trabajó sobre dos piezas principales:

* `contracts`: contiene las versiones finales de `CFP.sol` y `CFPFactory.sol`, adaptadas para este práctico.
* `api`: contiene la API REST que interactúa con esos contratos, firma operaciones con una cuenta derivada desde una mnemónica y persiste datos locales en SQLite.

Además, se incorporó un esquema de eventos para mantener consistencia entre lo que ocurre on chain y lo que se guarda en la base de datos local.

## Cómo se ejecuta

Primero hay que abrir una terminal en la carpeta `contracts` y levantar la red local de Hardhat:

```bash
npx hardhat node
```

Después, en otra terminal y también parado en `contracts`, se despliegan los contratos con el script de despliegue:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

La dirección resultante de `CFPFactory` debe cargarse luego en la API.

Por último, la API se ejecuta desde la carpeta `api` con:

```bash
uvicorn api:app --port 5000
```

## Variables de entorno

El archivo [api/.env.example](api/.env.example) muestra las variables requeridas para correr el proyecto, pero no obliga a usar un único mecanismo de carga. Se pueden definir en un archivo `.env`, exportarlas en la sesión, pasarlas inline al comando o usar cualquier otro método equivalente.

Las variables principales son:

* `WEB3_PROVIDER_URL`: URL del nodo JSON-RPC. En este práctico suele ser `http://localhost:8545`.
* `CFP_FACTORY_ADDRESS`: dirección del contrato `CFPFactory` desplegado.
* `CFP_MNEMONIC`: frase mnemónica usada para derivar la cuenta local con la que firma la API.
* `DERIVACION_PATH`: ruta HD de derivación. Por defecto se usa `m/44'/60'/0'/0/0`.
* `CFP_DB_PATH`: ruta del archivo SQLite donde se guardan los datos off chain.
* `CFP_ADMIN_ADDRESS`: dirección del administrador que autoriza y desautoriza cuentas.

## Estructura del proyecto

La organización principal del trabajo es esta:

```text
TP/9
├── README.md
├── api/
│   ├── api.py
│   ├── db/
│   ├── listeners/
│   ├── models/
│   ├── requests/
│   ├── services/
│   ├── test/
│   └── .env.example
├── contracts/
│   ├── contracts/
│   │   ├── CFP.sol
│   │   └── CFPFactory.sol
│   ├── scripts/
│   │   └── deploy.js
│   ├── test/
│   └── artifacts/
└── img/
```

Resumen de cada carpeta:

* `contracts/`: contiene el código Solidity, el script de despliegue, las pruebas y los artefactos generados por Hardhat.
* `api/`: contiene la aplicación REST, la lógica de acceso a contratos, validaciones, persistencia local y pruebas.
* `img/`: reúne imágenes usadas por la documentación.

## Contratos

### `CFP`

Representa un llamado a presentación de propuestas. Guarda el identificador del llamado, la dirección del creador, la fecha de cierre y las propuestas registradas.

Lo más importante del contrato es lo siguiente:

* Permite registrar propuestas antes del cierre.
* Evita duplicados.
* Emite `ProposalRegistered` cuando se registra una propuesta.
* Expone funciones informativas para consultar propuesta, cantidad, creador, cierre y timestamp de registro.

### `CFPFactory`

Es la factoría que crea instancias de `CFP` y administra quién está autorizado a crear llamados.

Lo esencial del contrato es:

* Gestiona registro, autorización y desautorización de creadores.
* Emite eventos como `CreatorRegistered`, `CreatorAuthorized`, `CreatorUnauthorized` y `CFPCreated`.
* Permite crear llamados directamente o en nombre de otra cuenta cuando lo hace el dueño.
* Expone consultas sobre creador, pendientes, autorizados y llamados creados.

## API y endpoints

La API conecta con el nodo local por HTTP, lee la dirección del factory desde el entorno y trabaja con una cuenta derivada de la mnemónica configurada. Además, escucha eventos para que la base de datos local refleje solo transacciones realmente confirmadas.

Los endpoints se agrupan así:

* Creación y consulta de llamados: `/create`, `/calls/:call_id`, `/closing-time/:call_id`.
* Registro de usuarios y autorizaciones: `/register`, `/registrations/:address`, `/authorized/:address`, `/admin/nonce`, `/authorize/:address`, `/unauthorize/:address`.
* Registro y verificación de propuestas: `/register-proposal`, `/proposal-data/:call_id/:proposal`, `/verify-proof`.
* Información del contrato: `/contract-address`, `/contract-owner`.

En líneas generales, `/create` registra el llamado a nivel local, `/register-proposal` calcula y registra la propuesta anónima usando una raíz de Merkle, y los endpoints de autorización permiten administrar quién puede crear llamados.

## Conclusiones

El práctico completa la transición desde un sistema puramente on chain hacia una arquitectura híbrida. Los contratos siguen siendo la fuente de verdad para lo que debe ser verificable, mientras que la API resuelve la parte operativa: firmas, validaciones, persistencia local y exposición por REST.

La decisión de usar hashes, árboles de Merkle, eventos y SQLite permite bajar costos de almacenamiento, mantener trazabilidad y ofrecer una interfaz más simple para operar el sistema sin perder verificabilidad.
