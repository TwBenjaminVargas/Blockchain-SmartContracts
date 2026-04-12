# Trabajo práctico 4

## Descripción general

Este trabajo práctico implementa un servicio de sellado de archivos apoyado en un contrato inteligente ya desplegado en la red de testeo de la BFA. El contrato expone una interfaz de consulta y registro de hashes, y su dirección junto con su ABI se encuentran definidos en [Stamper.json](Stamper.json).

La solución desarrollada se compone de dos partes principales:

1. Un servidor de API REST implementado en Python con Flask y Web3, encargado de interactuar con el contrato.
2. Una aplicación web estática que permite seleccionar archivos, calcular su hash SHA-256 y solicitar su verificación o registro mediante la API.

## Estructura del repositorio

La organización del directorio `4/` es la siguiente:

```text
4/
├── README.md
├── Stamper.json
├── openapi.yaml
├── api/
│   └── python/
│       ├── apiserver.py
│       ├── README.md
│       ├── requirements.txt
│       └── test_apiserver.py
├── app web/
    ├── app.js
    ├── index.html
    └── style.css

```

### Finalidad de cada componente

- `Stamper.json`: contiene la ABI del contrato y la información de despliegue utilizada por la API.
- `openapi.yaml`: especificación formal de la interfaz REST.
- `api/python/apiserver.py`: implementación del servidor REST.
- `app web/index.html`, `app web/app.js`, `app web/style.css`: interfaz web cliente.

## Requisitos previos

Para ejecutar la solución es necesario disponer de los siguientes elementos:

- Python 3.10 o superior.
- Un nodo Ethereum accesible mediante IPC en una ruta equivalente a la utilizada por la implementación.
- Al menos una cuenta válida en `~/.ethereum/keystore`.
- La contraseña de descifrado de la primera cuenta del keystore, ordenada lexicográficamente.

La implementación asume, por defecto, que el nodo se encuentra en `~/blockchain-iua/bfatest/node/geth.ipc`. Si la instalación local utiliza otra ruta, dicho valor debe ajustarse en [api/python/apiserver.py](api/python/apiserver.py).

## Ejecución del servidor de API

El servidor puede iniciarse de dos maneras, según el mecanismo elegido para proporcionar la contraseña de la cuenta:

```bash
python3 api/python/apiserver.py -p "CONTRASENA"
```

o bien:

```bash
python3 api/python/apiserver.py -f /ruta/al/archivo_con_la_contraseña.txt
```

Durante el arranque, el programa realiza las siguientes acciones:

1. Conecta el cliente Web3 al nodo configurado.
2. Carga el contrato a partir de [Stamper.json](Stamper.json).
3. Localiza la primera cuenta del directorio `~/.ethereum/keystore` en orden lexicográfico.
4. Descifra la clave privada utilizando la contraseña suministrada.
5. Habilita el middleware de firmado para poder enviar transacciones desde una cuenta local.

Una vez iniciado, el servidor expone la API en `http://127.0.0.1:5000`.

## Uso de la API REST

La interfaz sigue la especificación definida en [openapi.yaml](openapi.yaml) y en el contrato asociado.

### Consulta de un hash

```bash
curl http://127.0.0.1:5000/stamped/0x836a97e0ff6a85dd2746a39ed71171595759c02beda2d45d0280e0cd19ba3c34
```

Si el hash fue registrado, la respuesta contiene la dirección del firmante y el número de bloque correspondiente.

### Registro de un hash

```bash
curl -X POST http://127.0.0.1:5000/stamp \
  -H "Content-Type: application/json" \
  -d '{"hash":"0x..."}'
```

Si se desea registrar una firma adicional, el cuerpo JSON puede incluir el campo `signature`.

## Ejecución de la aplicación web

La interfaz web es estática y debe servirse desde un servidor HTTP local. Una forma simple de hacerlo es la siguiente:

```bash
cd "/home/ben/Documentos/ByCI/TP/4/app web"
python3 -m http.server 8000
```

Luego, abrir en el navegador la dirección:

```text
http://127.0.0.1:8000
```

Vista previa de la aplicación web:

![Vista de la aplicación Web Stamper](https://lh3.googleusercontent.com/u/0/d/12cYm1PuRAIAWAmbRIR-lqIWF8gRv_62J)

Funcionamiento de la interfaz:

1. El usuario selecciona un archivo local.
2. La aplicación calcula su hash SHA-256 en el navegador.
3. Opcionalmente, el usuario puede indicar una clave privada para firmar el hash.
4. La interfaz envía la solicitud `POST /stamp` a la API.
5. La respuesta informa si el archivo quedó registrado o si ya existía un sello previo.

La aplicación web utiliza `ethers.js` desde el navegador y comunica las solicitudes contra `http://127.0.0.1:5000`.

## Observaciones técnicas

- Los hashes, direcciones y firmas se manejan como cadenas hexadecimales con prefijo `0x`.
- Los valores numéricos se exponen en formato decimal.
- La API distingue entre errores de validación, ausencia de registros y conflictos por duplicación de hash.
- La documentación formal de los códigos de respuesta y los esquemas de datos se encuentra en [openapi.yaml](openapi.yaml).
