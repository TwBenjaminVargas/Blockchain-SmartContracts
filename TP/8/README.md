# Trabajo Práctico 8

## Introducción

En este trabajo práctico se implementó una API REST para interactuar con los contratos `CFP` y `CFPFactory` desarrollados en el TP 7. La aplicación expone endpoints para crear llamados a presentación de propuestas, registrar usuarios autorizados, registrar propuestas de forma anónima y consultar información on-chain asociada a cada llamado.

La solución está pensada para ejecutarse contra una red local de Hardhat, usando una cuenta derivada desde una frase mnemónica BIP39 y una dirección de contrato ya desplegada. La API consume las ABIs almacenadas en `api/src/` y se conecta al nodo mediante HTTP.

## Despliegue

### 1. Despliegue de contratos

Antes de ejecutar cualquier paso, conviene instalar las dependencias del proyecto del TP 7 si todavía no están presentes:

```bash
npm install
```

Este comando descarga e instala las dependencias necesarias para compilar y desplegar los contratos.

### 2. Levantar la red local

Antes de desplegar los contratos, hay que iniciar el nodo local de Hardhat desde la carpeta `TP/7`:

```bash
npx hardhat node
```

Este comando levanta una blockchain local con cuentas prefundidas y un endpoint JSON-RPC disponible en `http://localhost:8545`. La API y el script de despliegue se conectan a ese nodo para firmar y enviar transacciones.

### 3. Preparar el script de despliegue

Desde la carpeta `TP/8`, se copia el script de despliegue hacia el proyecto del TP 7 y se agregan reglas locales de ignore:

```bash
cp deploy.js ../7/ && echo -e ".gitignore\ndeploy.js" >> ../7/.gitignore
```

`cp deploy.js ../7/` mueve el helper de despliegue al proyecto donde viven los contratos, para ejecutar el despliegue junto con `hardhat`. La segunda parte extiende el `.gitignore` del TP 7 para que ese archivo auxiliar y los cambios locales de ignore no queden versionados ni generen ruido de control de cambios cuando se descarga o sincroniza el proyecto.

### 4. Variables de entorno para el despliegue

El script `deploy.js` requiere la variable `CFP_MNEMONIC`, que debe contener la frase mnemónica desde la que se deriva la cuenta de despliegue. En este práctico se utiliza el path `m/44'/60'/0'/0/0`, es decir, el índice 0 de la cuenta del nodo local.

Ejemplos de carga de la variable:

```bash
CFP_MNEMONIC="test test test test test test test test test test test junk" npx hardhat run deploy.js --network localhost
```

También puede cargarse de otras formas:

```bash
export CFP_MNEMONIC="test test test test test test test test test test test junk"
```

o definiéndola en un archivo `.env` que luego sea consumido por la sesión o por la herramienta que ejecute el script.

### 5. Desplegar el contrato

Con la red local ya activa y la variable `CFP_MNEMONIC` disponible, el despliegue se ejecuta con:

```bash
npx hardhat run deploy.js --network localhost
```

Este comando compila y ejecuta el script contra la red local, derivando la cuenta correcta desde la frase mnemónica y desplegando `CFPFactory`. La dirección resultante debe guardarse luego en `CFP_FACTORY_ADDRESS` para que la API pueda conectarse al contrato desplegado.

## Estructura del proyecto

La parte relevante de `TP/8` queda organizada así:

```text
.
├── api
│   ├── api.py
│   └── src
│       ├── cfp_abi.json
│       ├── cfp_factory_abi.json
│       ├── contractManager.py
│       ├── schemas.py
│       ├── settings.py
│       └── signer.py
├── deploy.js
├── messages.py
├── README.md
├── requirements.txt
├── test_apiserver.py
└── .env.example
```

Las ABIs de los contratos se encuentran en `api/src/`, junto con la lógica de acceso al contrato, la carga de configuración y el firmador usado por la API.

## API REST

### Variables de entorno y configuración

La API puede configurarse de distintas maneras, pero la forma documentada y recomendada es copiar `.env.example` a un archivo llamado `.env` en la raíz de `TP/8` y completar sus valores. El servidor también puede recibir las variables por exportación directa en la sesión o por prefijo inline al ejecutar el comando.

Las variables que consume el servicio son:

- `WEB3_PROVIDER_URL`: URL del nodo JSON-RPC, normalmente `http://localhost:8545`.
- `CFP_FACTORY_ADDRESS`: dirección del contrato `CFPFactory` desplegado.
- `CFP_MNEMONIC`: frase mnemónica usada para derivar la cuenta local.
- `DERIVACION_PATH`: ruta de derivación HD, por defecto `m/44'/60'/0'/0/0`.

### Ejecución de la API

Para levantar el servidor hay que ubicarse en la carpeta `TP/8/api` y ejecutar:

```bash
uvicorn api:app --reload --port 5000
```

`uvicorn` arranca la aplicación FastAPI en el puerto `5000`; la opción `--reload` habilita recarga automática durante el desarrollo.

## Endpoints

La API expone las siguientes rutas, que cubren la creación de llamados, el alta de usuarios autorizados, el registro anónimo de propuestas y las consultas de estado sobre contratos y datos asociados.

### `/create`

* Crea un llamado a presentación de propuestas utilizando la función correspondiente de `CFPFactory`.
* Método: `POST`
* Content-type: `application/json`
* Cuerpo: Un objeto JSON con los siguientes campos:
  * `callId`: Hash que identifica al llamado.
  * `closingTime`: Fecha y hora del cierre de convocatoria, expresada en formato ISO 8601.
  * `signature`: Firma, con la clave privada del que hace la llamada, de la dirección del contrato concatenada con `callId` y con `closingTime`. La API utiliza la dirección que se deriva de la firma para asignarle la propiedad del llamado creado. El mensaje a firmar es una secuencia de bytes de longitud 84. Los primeros 20 bytes son la dirección del contrato, los siguientes 32 bytes son el `callId`, y los últimos 32 bytes son el *timestamp* correspondiente al `closingTime`, codificado como un entero *big endian* de 32 bytes. Antes de ser firmado, al mensaje se le agrega el prefijo estándar de Ethereum `\x19Ethereum Signed Message:\n` seguido de la longitud del mensaje en bytes en formato decimal ASCII, para evitar confusión con la firma de transacciones.  En el caso de la biblioteca `web3` de Python, esto equivale a que el mensaje sea procesado por la función `encode_defunct` de `eth_account.messages` de la biblioteca `eth-account` de Python previo a la firma.
* Retorno exitoso:
  * Código HTTP: 201
  * Cuerpo: Un objeto JSON con un campo "message" con valor OK.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                          | Código | Mensaje              |
    |--------------------------------|--------|----------------------|
    | Content-Type incorrecto        | 400    | INVALID_MIMETYPE     |
    | campo requerido ausente        | 400    | MISSING_FIELD        |
    | callId mal formado             | 400    | INVALID_CALLID       |
    | closingTime mal formado        | 400    | INVALID_TIME_FORMAT  |
    | callId ya existente            | 403    | ALREADY_CREATED      |
    | emisor no autorizado           | 403    | UNAUTHORIZED         |
    | tiempo de cierre inválido      | 400    | INVALID_CLOSING_TIME |
    | firma inválida                 | 400    | INVALID_SIGNATURE    |
    | desconocida                    | 500    | INTERNAL_ERROR       |

### `/register`

* Permite a un usuario registrarse para crear llamados, y los autoriza de inmediato.
* Método: `POST`
* Content-type: `application/json`
* Cuerpo: Un objeto JSON con los siguientes campos:
  * `address`: Dirección del solicitante.
  * `signature`: Firma de la dirección del contrato con la clave privada del solicitante. El mensaje a firmar es una secuencia de bytes de longitud 20. Antes de ser firmado, al mensaje se le agrega el prefijo estándar de Ethereum `\x19Ethereum Signed Message:\n` seguido de la longitud del mensaje en bytes en formato decimal ASCII, para evitar confusión con la firma de transacciones. En el caso de la biblioteca `web3` de Python, esto equivale a que el mensaje sea procesado por la función `encode_defunct` de `eth_account.messages` de la biblioteca `eth-account` de Python previo a la firma. La API verifica que la dirección recuperada de la firma coincida con el campo `address`.
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con un campo "message" con valor OK.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                          | Código | Mensaje              |
    |--------------------------------|--------|----------------------|
    | Content-Type incorrecto        | 400    | INVALID_MIMETYPE     |
    | campo requerido ausente        | 400    | MISSING_FIELD        |
    | dirección inválida             | 400    | INVALID_ADDRESS      |
    | ya estaba autorizado           | 403    | ALREADY_AUTHORIZED   |
    | firma inválida                 | 400    | INVALID_SIGNATURE    |
    | desconocida                    | 500    | INTERNAL_ERROR       |

### `/register-proposal`

* Permite a un usuario registrar una propuesta en un determinado llamado. Este registro es anónimo, es decir, la dirección que quedará registrada en el contrato es la utilizada por el servidor de la API.
* Método: `POST`
* Content-type: `application/json`
* Cuerpo: Un objeto JSON con los siguientes campos:
  * `callId`: Hash que identifica al llamado.
  * `proposal`: Hash que identifica a la propuesta.
* Retorno exitoso:
  * Código HTTP: 201
  * Cuerpo: Un objeto JSON con un campo "message" con valor OK.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                          | Código | Mensaje              |
    |--------------------------------|--------|----------------------|
    | Content-Type incorrecto        | 400    | INVALID_MIMETYPE     |
    | campo requerido ausente        | 400    | MISSING_FIELD        |
    | callId mal formado             | 400    | INVALID_CALLID       |
    | callId inexistente             | 404    | CALLID_NOT_FOUND     |
    | propuesta mal formada          | 400    | INVALID_PROPOSAL     |
    | propuesta ya existente         | 403    | ALREADY_REGISTERED   |
    | desconocida                    | 500    | INTERNAL_ERROR       |

### `/authorized/:address`

* Método: `GET`
* Argumento: `:address` corresponde a una dirección
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con un campo booleano
    * "authorized", el estado de autorización de la dirección provista.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                    | Código |  Mensaje             |
    |--------------------------|--------|----------------------|
    |dirección inválida        | 400    | INVALID_ADDRESS      |
    |desconocida               | 500    | INTERNAL_ERROR       |

### `/calls/:call_id`

* Método: `GET`
* Argumento: `:call_id` es el hash que identifica a un llamado
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con dos campos de tipo `string`:
    * "creator", la dirección del creador del llamado.
    * "cfp", la dirección del contrato que representa al llamado.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                    | Código |  Mensaje             |
    |--------------------------|--------|----------------------|
    |callId mal formado        | 400    | INVALID_CALLID       |
    |callId inexistente        | 404    | CALLID_NOT_FOUND     |
    |desconocida               | 500    | INTERNAL_ERROR       |

### `/closing-time/:call_id`

* Método: `GET`
* Argumento: `:call_id` es el hash que identifica a un llamado
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con un campo de tipo `string`:
    * "closingTime", la fecha y hora de cierre del llamado, en formato ISO 8601.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                    | Código |  Mensaje             |
    |--------------------------|--------|----------------------|
    |callId mal formado        | 400    | INVALID_CALLID       |
    |callId inexistente        | 404    | CALLID_NOT_FOUND     |
    |desconocida               | 500    | INTERNAL_ERROR       |

### `/contract-address`

* Método: `GET`
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con un campo de tipo `string`:
    * "address", dirección del contrato factoría.

### `/contract-owner`

* Método: `GET`
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con un campo de tipo `string`:
    * "address", dirección del dueño del contrato factoría.

### `/proposal-data/:call_id/:proposal`

* Método: `GET`
* Argumentos:
  * `:call_id` es el hash que identifica a un llamado.
  * `:proposal` es el hash que identifica una propuesta.
* Retorno exitoso:
  * Código HTTP: 200
  * Cuerpo: Un objeto JSON con tres campos:
    * "sender", de tipo "string" con la dirección del que envió la propuesta.
    * "blockNumber", de tipo "number" con el número de bloque en el cual se registró.
    * "timestamp", de tipo string, con la fecha y hora de registro en formato ISO 8601.
* Retorno fallido:
  * Código HTTP: Según la tabla siguiente.
  * Cuerpo: Un objeto JSON con un campo "message" con valor indicado en la tabla siguiente.

    | Causa                    | Código |  Mensaje             |
    |--------------------------|--------|----------------------|
    |callId mal formado        | 400    | INVALID_CALLID       |
    |callId inexistente        | 404    | CALLID_NOT_FOUND     |
    |propuesta mal formada     | 400    | INVALID_PROPOSAL     |
    |propuesta inexistente     | 404    | PROPOSAL_NOT_FOUND   |
    |desconocida               | 500    | INTERNAL_ERROR       |

## Mensajes

| ID                  | Mensaje                               |
|---------------------|---------------------------------------|
| INVALID_ADDRESS     | "Dirección inválida"                  |
| INVALID_SIGNATURE   | "Firma inválida"                      |
| INVALID_MIMETYPE    | "Tipo MIME inválido"                  |
| INVALID_CALLID      | "Identificador de llamado incorrecto" |
| INVALID_PROPOSAL    | "Formato de propuesta incorrecto"     |
| INVALID_TIME_FORMAT | "Formato de tiempo incorrecto"        |
| INVALID_CLOSING_TIME| "Tiempo de cierre inválido"           |
| MISSING_FIELD       | "Campo requerido ausente"             |
| ALREADY_AUTHORIZED  | "Ya está autorizado"                  |
| ALREADY_CREATED     | "El llamado ya existe"                |
| ALREADY_REGISTERED  | "La propuesta ya ha sido registrada"  |
| CALLID_NOT_FOUND    | "El llamado no existe"                |
| PROPOSAL_NOT_FOUND  | "La propuesta no existe"              |
| UNAUTHORIZED        | "No autorizado"                       |
| INTERNAL_ERROR      | "Error interno"                       |
| OK                  | "OK"                                  |

## Conclusión

El práctico integró despliegue local, derivación de cuentas desde una frase mnemónica, firmas de mensajes y consumo de contratos desde una API REST. La solución quedó preparada para ejecutarse sobre Hardhat en una red local y documentada para que el despliegue y la API puedan reproducirse sin tocar el código fuente.
